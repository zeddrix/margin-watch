<script lang="ts">
	import { tick } from 'svelte';
	import { WHAT_TO_CHECK } from '../checks';
	import { formatMoney, formatPct, formatPts } from '../format';
	import type { Job } from '../types';
	import BulletChart from './BulletChart.svelte';
	import StatusPill from './StatusPill.svelte';

	let { job, onClose }: { job: Job; onClose: () => void } = $props();

	let panel = $state<HTMLElement | null>(null);
	let closeButton = $state<HTMLButtonElement | null>(null);

	const review = $derived(job.status === 'NEEDS_REVIEW');
	const flagged = $derived(job.status !== 'ON_TRACK' && !review);

	$effect(() => {
		// Move focus into the dialog when it opens (and when it switches to another job).
		void job.id;
		tick().then(() => closeButton?.focus());
	});

	function focusables(): HTMLElement[] {
		if (!panel) return [];
		return [
			...panel.querySelectorAll<HTMLElement>(
				'a[href], button:not([disabled]), input, select, summary, [tabindex]:not([tabindex="-1"])'
			)
		].filter((el) => el.offsetParent !== null || el === document.activeElement);
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			event.preventDefault();
			onClose();
			return;
		}
		if (event.key !== 'Tab' || !panel) return;
		const items = focusables();
		if (items.length === 0) {
			event.preventDefault();
			return;
		}
		const first = items[0];
		const last = items[items.length - 1];
		const active = document.activeElement;
		const inside = active instanceof Node && panel.contains(active);
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
		data-testid="drawer-backdrop"
		tabindex="-1"
		aria-label="Close job details"
		onclick={onClose}
	></button>
	<div
		class="drawer"
		role="dialog"
		aria-modal="true"
		aria-labelledby="drawer-title"
		data-testid="job-drawer"
		bind:this={panel}
	>
		<header>
			<div class="title-block">
				<p class="eyebrow">{job.client}</p>
				<h2 id="drawer-title" data-testid="drawer-title">{job.id} {job.name}</h2>
				<p class="meta">{job.site}</p>
				<p class="meta">PM {job.project_manager} · {job.stage}</p>
			</div>
			<button type="button" class="close" bind:this={closeButton} onclick={onClose}>
				<svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16">
					<path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
				</svg>
				<span class="sr-only">Close</span>
			</button>
		</header>

		<div class="body">
			<div class="status" data-testid="drawer-status"><StatusPill status={job.status} /></div>

			{#if review}
				<section class="block review" data-testid="drawer-review">
					<h3>Data problem</h3>
					<p>{job.reason}</p>
					<p class="note">
						The job wasn't assessed, so no margin figures are shown. Nothing is guessed.
					</p>
				</section>
				<section class="block check" data-testid="drawer-check">
					<h3>What to check in Simpro</h3>
					<p>{WHAT_TO_CHECK[job.review_code ?? ''] ?? 'Check this job’s data in Simpro.'}</p>
				</section>
			{:else}
				<section class="block">
					<h3>{flagged ? 'Why it’s flagged' : 'How it’s tracking'}</h3>
					<p data-testid="drawer-why">{job.reason}</p>
				</section>
				<dl class="figures num">
					<div><dt>Quoted margin</dt><dd data-testid="drawer-quoted">{formatPct(job.quoted_margin_pct)}</dd></div>
					<div><dt>Forecast margin</dt><dd data-testid="drawer-forecast">{formatPct(job.forecast_margin_pct)}</dd></div>
					<div><dt>Erosion</dt><dd data-testid="drawer-erosion">{formatPts(job.margin_erosion_pts)}</dd></div>
					<div><dt>Dollars at risk</dt><dd data-testid="drawer-at-risk">{formatMoney(job.dollars_at_risk)}</dd></div>
				</dl>
				<p class="note">
					Sell {formatMoney(job.quoted_sell_ex_gst)} ex GST · {formatPct(job.percent_complete)} complete.
					Forecasts are projected at the current burn rate.
				</p>
			{/if}

			<section class="block">
				<h3>Cost centres</h3>
				{#if !review}
					<p class="legend">
						<span class="key estimate" aria-hidden="true"></span>Estimate
						<span class="key actual" aria-hidden="true"></span>Spent
						<span class="key marker" aria-hidden="true"></span>Forecast
						<span class="key overrun" aria-hidden="true"></span>Overrun
					</p>
				{/if}
				<div class="charts">
					{#each job.cost_centres as centre (centre.name)}
						<BulletChart {centre} />
					{/each}
				</div>
			</section>
		</div>
	</div>
</div>

<style>
	.root {
		position: fixed;
		inset: 0;
		z-index: 20;
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
	.drawer {
		position: absolute;
		top: 0;
		right: 0;
		bottom: 0;
		width: min(520px, 100%);
		background: var(--surface);
		border-left: 1px solid var(--border);
		box-shadow: var(--shadow-drawer);
		overflow-y: auto;
		overscroll-behavior: contain;
		animation: slide 180ms ease-out;
	}
	header {
		position: sticky;
		top: 0;
		z-index: 1;
		background: var(--surface);
		display: flex;
		gap: 16px;
		justify-content: space-between;
		align-items: flex-start;
		padding: 20px 24px 16px;
		border-bottom: 1px solid var(--border);
	}
	.eyebrow {
		margin: 0;
		font-size: 13px;
		color: var(--muted);
	}
	h2 {
		margin: 2px 0 4px;
		font-size: 18px;
		line-height: 1.3;
	}
	.meta {
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
	.close:hover {
		background: var(--surface-muted);
	}
	.body {
		padding: 16px 24px 32px;
		display: grid;
		gap: 20px;
		align-content: start;
	}
	.block h3 {
		margin: 0 0 6px;
		font-size: 13px;
		font-weight: 700;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.block p {
		margin: 0;
		font-size: 15px;
	}
	.review {
		padding: 12px 16px;
		border-radius: 8px;
		background: var(--review-bg);
		border: 1px solid var(--review-border);
	}
	.check {
		padding: 12px 16px;
		border-radius: 8px;
		border: 1px solid var(--border);
	}
	.note {
		margin: 6px 0 0 !important;
		font-size: 13px !important;
		color: var(--muted);
	}
	.figures {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 8px;
		margin: 0;
	}
	.figures div {
		padding: 10px 12px;
		border: 1px solid var(--border);
		border-radius: 8px;
	}
	dt {
		font-size: 13px;
		color: var(--muted);
	}
	dd {
		margin: 2px 0 0;
		font-size: 18px;
		font-weight: 700;
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 12px;
		font-size: 13px !important;
		color: var(--muted);
		margin-bottom: 12px !important;
	}
	.key {
		display: inline-block;
		width: 12px;
		height: 10px;
		border-radius: 2px;
		margin-right: -6px;
	}
	.key.estimate {
		background: var(--bar-estimate);
	}
	.key.actual {
		background: var(--bar-actual);
		height: 4px;
	}
	.key.marker {
		background: var(--bar-marker);
		width: 3px;
		height: 12px;
	}
	.key.overrun {
		background: var(--loss-strong);
	}
	.charts {
		display: grid;
		gap: 16px;
	}
	@keyframes slide {
		from {
			transform: translateX(24px);
			opacity: 0;
		}
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
	}
	@media (max-width: 640px) {
		header {
			padding: 16px;
		}
		.body {
			padding: 16px 16px 32px;
		}
	}
</style>
