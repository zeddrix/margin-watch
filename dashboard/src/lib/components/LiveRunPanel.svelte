<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { startLiveRun, type LiveEvent, type LiveStep, type NumberCheck } from '../live';
	import { STATUS_CHIP, STATUS_ORDER } from '../status';
	import type { Status } from '../types';

	type StepEvent = Extract<LiveEvent, { type: 'step' }>;
	type State = 'pending' | 'running' | 'done' | 'warning' | 'error';
	interface StepView extends LiveStep {
		state: State;
		detail: string;
		data: StepEvent['data'];
	}

	let {
		base,
		onClose,
		onFinished
	}: {
		base: string;
		onClose: () => void;
		onFinished: (asOf: string) => void;
	} = $props();

	let steps = $state<StepView[]>([]);
	let phase = $state<'running' | 'done' | 'error'>('running');
	let lastAi = $state<'demo' | 'demo-bad'>('demo');
	let errorMessage = $state('');
	let dialog = $state<HTMLElement | null>(null);
	let closeButton = $state<HTMLButtonElement | null>(null);
	let resultsButton = $state<HTMLButtonElement | null>(null);

	const finished = $derived(steps.filter((s) => s.state === 'done' || s.state === 'warning').length);
	const percent = $derived(steps.length ? Math.round((finished / steps.length) * 100) : 0);

	async function run(ai: 'demo' | 'demo-bad') {
		lastAi = ai;
		phase = 'running';
		errorMessage = '';
		steps = [];
		try {
			for await (const event of startLiveRun(fetch, base, ai)) {
				if (event.type === 'start') {
					steps = event.steps.map((s) => ({ ...s, state: 'pending', detail: '', data: undefined }));
				} else if (event.type === 'step') {
					const step = steps.find((s) => s.id === event.step);
					if (step) {
						step.state = event.state;
						step.detail = event.detail ?? step.detail;
						step.data = event.data ?? step.data;
						void follow(step.id);
					}
				} else if (event.type === 'done') {
					phase = 'done';
					onFinished(event.as_of);
					await tick();
					resultsButton?.focus();
				} else {
					const step = steps.find((s) => s.id === event.step);
					if (step) step.state = 'error';
					errorMessage = event.message;
					phase = 'error';
				}
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : String(error);
			phase = 'error';
		}
	}

	/** Keep the step that just changed on screen, so the viewer can follow the run. */
	async function follow(id: string) {
		await tick();
		const element = dialog?.querySelector(`[data-testid="live-step-${id}"]`);
		const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		element?.scrollIntoView({ block: 'nearest', behavior: reduce ? 'auto' : 'smooth' });
	}

	/** Money, percentages and points are shown one by one; ids and counts are summarised. */
	function isFigure(token: string): boolean {
		return /[$%]|pts/.test(token);
	}

	onMount(() => {
		closeButton?.focus();
		void run('demo');
	});

	function counts(data: StepEvent['data']): [Status, number][] {
		const tally = data?.counts;
		return tally ? STATUS_ORDER.map((s) => [s, tally[s] ?? 0] as [Status, number]) : [];
	}

	function checks(data: StepEvent['data']): NumberCheck[] {
		return data?.checks ?? [];
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			event.preventDefault();
			onClose();
			return;
		}
		if (event.key !== 'Tab' || !dialog) return;
		const items = [
			...dialog.querySelectorAll<HTMLElement>('a[href], button:not([disabled])')
		].filter((el) => el.offsetParent !== null);
		if (items.length === 0) return;
		const first = items[0];
		const last = items[items.length - 1];
		const active = document.activeElement;
		const inside = active instanceof Node && dialog.contains(active);
		if (event.shiftKey && (active === first || !inside)) {
			event.preventDefault();
			last.focus();
		} else if (!event.shiftKey && (active === last || !inside)) {
			event.preventDefault();
			first.focus();
		}
	}
</script>

<svelte:window onkeydown={onKeydown} />

<div class="root">
	<button
		type="button"
		class="backdrop"
		tabindex="-1"
		aria-label="Close the live run"
		onclick={onClose}
	></button>
	<div
		class="panel"
		role="dialog"
		aria-modal="true"
		aria-labelledby="live-title"
		data-testid="live-panel"
		bind:this={dialog}
	>
		<header>
			<div>
				<p class="eyebrow">Dry run · nothing is sent</p>
				<h2 id="live-title" data-testid="live-title">Morning check · dry run</h2>
				<p class="sub">
					Running the real program on the sample jobs, step by step. Slowed down so you can
					follow it.
				</p>
			</div>
			<button type="button" class="close" bind:this={closeButton} onclick={onClose}>
				<svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16">
					<path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
				</svg>
				<span class="sr-only">Close</span>
			</button>
		</header>

		<div
			class="progress"
			role="progressbar"
			aria-label="Steps finished"
			aria-valuemin="0"
			aria-valuemax={steps.length || 7}
			aria-valuenow={finished}
		>
			<span class="bar" class:warn={lastAi === 'demo-bad' && phase !== 'running'} style:width="{percent}%"></span>
		</div>

		<ol class="steps" aria-live="polite">
			{#each steps as step, index (step.id)}
				<li class="step" data-state={step.state} data-testid="live-step-{step.id}">
					<span class="marker" aria-hidden="true">
						{#if step.state === 'running'}
							<span class="spinner"></span>
						{:else if step.state === 'done'}
							<svg viewBox="0 0 16 16" width="14" height="14"><path d="m3.5 8.3 2.8 2.8 6.2-6.4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" /></svg>
						{:else if step.state === 'warning'}
							<svg viewBox="0 0 16 16" width="14" height="14"><path d="M8 3.5v5.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" /><circle cx="8" cy="12" r="1.2" fill="currentColor" /></svg>
						{:else if step.state === 'error'}
							<svg viewBox="0 0 16 16" width="14" height="14"><path d="M4.5 4.5l7 7M11.5 4.5l-7 7" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" /></svg>
						{:else}
							{index + 1}
						{/if}
					</span>
					<div class="content">
						<p class="title">
							{step.title}
							<span class="sr-only">
								— {step.state === 'pending' ? 'waiting' : step.state === 'running' ? 'in progress' : step.state === 'warning' ? 'needs attention' : step.state}
							</span>
						</p>
						{#if step.detail}
							<p class="detail">{step.detail}</p>
						{/if}

						{#if step.id === 'maths' && step.data?.counts}
							<div class="tally" data-testid="live-tally">
								{#each counts(step.data) as [status, count] (status)}
									<span class="chip" data-tone={status}>
										<span class="dot" aria-hidden="true"></span>{STATUS_CHIP[status]}
										<strong class="num">{count}</strong>
									</span>
								{/each}
								{#if step.data.dollars_at_risk}
									<span class="money num">{step.data.dollars_at_risk} forecast over budget</span>
								{/if}
							</div>
						{/if}

						{#if step.id === 'review' && step.data?.jobs?.length}
							<ul class="review" data-testid="live-review">
								{#each step.data.jobs as job (job.id)}
									<li><span class="num job-id">{job.id}</span> {job.name}: <span class="muted">{job.problem}</span></li>
								{/each}
							</ul>
						{/if}

						{#if step.id === 'summary' && checks(step.data).length}
							<p class="checks-label">Every number in the AI's answer, checked against the calculations:</p>
							<ul class="checks">
								{#each checks(step.data).filter((c) => !c.ok || isFigure(c.token)) as check, i (check.token)}
									<li
										class="check num"
										data-testid="live-check"
										data-ok={check.ok}
										style:animation-delay="{i * 40}ms"
									>
										{#if check.ok}
											<svg aria-hidden="true" viewBox="0 0 16 16" width="12" height="12"><path d="m3.5 8.3 2.8 2.8 6.2-6.4" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" /></svg>
											{check.token}<span class="sr-only"> matches</span>
										{:else}
											<svg aria-hidden="true" viewBox="0 0 16 16" width="12" height="12"><path d="M4.5 4.5l7 7M11.5 4.5l-7 7" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" /></svg>
											{check.token} <span class="bad-note">not in the calculations</span>
										{/if}
									</li>
								{/each}
							</ul>
							{#if checks(step.data).some((c) => c.ok && !isFigure(c.token))}
								<p class="also">
									Also matched: {checks(step.data).filter((c) => c.ok && !isFigure(c.token)).length}
									job numbers and counts.
								</p>
							{/if}
						{/if}

						{#if step.id === 'excel' && step.data?.href}
							<a class="action" href={step.data.href} download data-testid="live-excel-link">
								<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14"><path d="M8 2.5v7M5 6.8 8 9.8l3-3M3 12.5h10" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" /></svg>
								Open Excel report
							</a>
						{/if}
						{#if step.id === 'email' && step.data?.href}
							<a class="action" href={step.data.href} target="_blank" rel="noopener" data-testid="live-email-link">
								<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14"><rect x="2" y="3.5" width="12" height="9" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5" /><path d="m2.5 4.5 5.5 4 5.5-4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" /></svg>
								Preview email<span class="sr-only"> (opens in a new tab)</span>
							</a>
						{/if}
					</div>
				</li>
			{/each}
		</ol>

		<footer>
			{#if phase === 'done'}
				<p class="done" data-testid="live-done">Done. Nothing was sent.</p>
				<div class="buttons">
					<button type="button" class="primary" data-testid="live-results" bind:this={resultsButton} onclick={onClose}>
						See the results
					</button>
					{#if lastAi === 'demo'}
						<button type="button" class="secondary" data-testid="live-try-bad" onclick={() => run('demo-bad')}>
							Try it with a made-up AI number
						</button>
					{:else}
						<button type="button" class="secondary" data-testid="live-run-again" onclick={() => run('demo')}>
							Run it again normally
						</button>
					{/if}
				</div>
			{:else if phase === 'error'}
				<p class="error" data-testid="live-error" role="alert">{errorMessage}</p>
				<div class="buttons">
					<button type="button" class="secondary" onclick={() => run(lastAi)}>Try again</button>
				</div>
			{:else}
				<p class="running">Running… {finished} of {steps.length || 7} steps done</p>
			{/if}
		</footer>
	</div>
</div>

<style>
	.root {
		position: fixed;
		inset: 0;
		z-index: 30;
		display: grid;
		place-items: center;
		padding: 24px;
	}
	.backdrop {
		position: absolute;
		inset: 0;
		border: 0;
		padding: 0;
		background: var(--backdrop);
		cursor: default;
		animation: fade 180ms ease-out;
	}
	.panel {
		position: relative;
		width: min(720px, 100%);
		max-height: calc(100vh - 48px);
		overflow-y: auto;
		overscroll-behavior: contain;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: var(--radius);
		box-shadow: 0 24px 64px rgb(15 23 42 / 0.28);
		animation: rise 200ms ease-out;
	}
	header {
		position: sticky;
		top: 0;
		z-index: 1;
		background: var(--surface);
		display: flex;
		justify-content: space-between;
		gap: 16px;
		padding: 20px 24px 12px;
	}
	.eyebrow {
		margin: 0;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--accent);
	}
	h2 {
		margin: 2px 0 4px;
		font-size: 20px;
	}
	.sub {
		margin: 0;
		font-size: 13px;
		color: var(--muted);
	}
	.close {
		flex: none;
		display: grid;
		place-items: center;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		border: 1px solid var(--border-strong);
		background: var(--surface);
		color: var(--text);
		cursor: pointer;
	}
	.progress {
		height: 4px;
		margin: 0 24px;
		border-radius: 999px;
		background: var(--border);
		overflow: hidden;
	}
	.bar {
		display: block;
		height: 100%;
		background: var(--accent);
		transition: width 300ms ease-out;
	}
	.bar.warn {
		background: var(--risk-strong);
	}
	.steps {
		list-style: none;
		margin: 0;
		padding: 16px 24px 8px;
		display: grid;
		gap: 4px;
	}
	.step {
		display: grid;
		grid-template-columns: 28px 1fr;
		gap: 12px;
		padding: 10px 0;
		border-bottom: 1px solid var(--border);
		transition: opacity 200ms ease-out;
	}
	.step:last-child {
		border-bottom: 0;
	}
	.step[data-state='pending'] {
		opacity: 0.55;
	}
	.marker {
		width: 28px;
		height: 28px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		font-size: 13px;
		font-weight: 700;
		color: var(--muted);
		border: 1.5px solid var(--border-strong);
		background: var(--surface);
	}
	[data-state='running'] .marker {
		border-color: var(--accent);
	}
	[data-state='done'] .marker {
		background: var(--ok-bg);
		border-color: var(--ok-border);
		color: var(--ok-fg);
		animation: pop 220ms ease-out;
	}
	[data-state='warning'] .marker {
		background: var(--risk-bg);
		border-color: var(--risk-strong);
		color: var(--risk-fg);
		animation: pop 220ms ease-out;
	}
	[data-state='error'] .marker {
		background: var(--loss-bg);
		border-color: var(--loss-strong);
		color: var(--loss-fg);
	}
	.spinner {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		border: 2px solid var(--accent-soft);
		border-top-color: var(--accent);
		animation: spin 700ms linear infinite;
	}
	.content {
		min-width: 0;
	}
	.title {
		margin: 3px 0 0;
		font-size: 15px;
		font-weight: 600;
	}
	.detail {
		margin: 4px 0 0;
		font-size: 14px;
		color: var(--text);
		animation: fade 200ms ease-out;
	}
	[data-state='warning'] .detail {
		color: var(--risk-fg);
		font-weight: 600;
	}
	.tally {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px;
		margin-top: 8px;
	}
	.chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		padding: 2px 10px;
		border-radius: 999px;
		border: 1px solid var(--border-strong);
		animation: fade 200ms ease-out both;
	}
	.chip .dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--dot);
	}
	.chip[data-tone='LOSS'] {
		--dot: var(--loss-strong);
	}
	.chip[data-tone='AT_RISK'] {
		--dot: var(--risk-strong);
	}
	.chip[data-tone='WATCH'] {
		--dot: var(--watch-strong);
	}
	.chip[data-tone='NEEDS_REVIEW'] {
		--dot: var(--review-strong);
	}
	.chip[data-tone='ON_TRACK'] {
		--dot: var(--ok-fg);
	}
	.money {
		font-size: 13px;
		font-weight: 600;
		margin-left: 4px;
	}
	.review {
		margin: 8px 0 0;
		padding: 0;
		list-style: none;
		display: grid;
		gap: 4px;
		font-size: 13px;
	}
	.job-id,
	.muted {
		color: var(--muted);
	}
	.checks-label {
		margin: 10px 0 6px;
		font-size: 13px;
		color: var(--muted);
	}
	.checks {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.check {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-size: 13px;
		font-weight: 600;
		padding: 2px 8px;
		border-radius: 6px;
		background: var(--ok-bg);
		color: var(--ok-fg);
		border: 1px solid var(--ok-border);
		animation: pop 220ms ease-out both;
	}
	.check[data-ok='false'] {
		background: var(--loss-bg);
		color: var(--loss-fg);
		border-color: var(--loss-strong);
	}
	.also {
		margin: 6px 0 0;
		font-size: 13px;
		color: var(--muted);
	}
	.bad-note {
		font-weight: 500;
	}
	.action {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		margin-top: 8px;
		font-size: 14px;
		font-weight: 600;
		color: var(--accent);
		text-decoration: none;
		border: 1px solid var(--border-strong);
		border-radius: 8px;
		padding: 4px 12px;
	}
	.action:hover {
		border-color: var(--accent);
		background: var(--surface-muted);
	}
	footer {
		position: sticky;
		bottom: 0;
		background: var(--surface);
		border-top: 1px solid var(--border);
		padding: 14px 24px 18px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
	}
	footer p {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
	}
	.done {
		color: var(--ok-fg);
	}
	.running {
		color: var(--muted);
	}
	.error {
		color: var(--loss-fg);
	}
	.buttons {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}
	.primary,
	.secondary {
		font: inherit;
		font-size: 14px;
		font-weight: 600;
		border-radius: 8px;
		padding: 8px 16px;
		cursor: pointer;
	}
	.primary {
		background: var(--accent);
		color: var(--surface);
		border: 1px solid var(--accent);
	}
	.primary:hover {
		background: var(--accent-hover);
	}
	.secondary {
		background: var(--surface);
		color: var(--text);
		border: 1px solid var(--border-strong);
	}
	.secondary:hover {
		border-color: var(--accent);
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	@keyframes pop {
		from {
			transform: scale(0.85);
			opacity: 0;
		}
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
	}
	@keyframes rise {
		from {
			transform: translateY(12px);
			opacity: 0;
		}
	}
	@media (max-width: 640px) {
		.root {
			padding: 0;
			place-items: stretch;
		}
		.panel {
			max-height: 100vh;
			border-radius: 0;
			width: 100%;
		}
		header,
		footer {
			padding-left: 16px;
			padding-right: 16px;
		}
		.steps {
			padding: 12px 16px 8px;
		}
		.progress {
			margin: 0 16px;
		}
	}
</style>
