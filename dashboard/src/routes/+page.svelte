<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { previousRunEntry, worsenedJobIds } from '../lib/compare';
	import { RunFileError, fetchIndex, fetchRun } from '../lib/load';
	import { fetchLiveHealth } from '../lib/live';
	import LiveRunPanel from '../lib/components/LiveRunPanel.svelte';
	import type { Job, Run, RunIndex } from '../lib/types';
	import JobDrawer from '../lib/components/JobDrawer.svelte';
	import JobsSection from '../lib/components/JobsSection.svelte';
	import KpiTiles from '../lib/components/KpiTiles.svelte';
	import SummaryCard from '../lib/components/SummaryCard.svelte';
	import TopBar from '../lib/components/TopBar.svelte';

	type Phase = 'loading' | 'empty' | 'index-error' | 'ready';

	let phase = $state<Phase>('loading');
	let index = $state<RunIndex | null>(null);
	let indexError = $state('');
	let selected = $state<string | null>(null);
	let run = $state<Run | null>(null);
	let previous = $state<Run | null>(null);
	let runError = $state<string | null>(null);
	let runLoading = $state(false);
	let openJob = $state<Job | null>(null);
	let returnFocus: HTMLElement | null = null;
	let live = $state(false);
	let showLive = $state(false);
	let runButton = $state<HTMLButtonElement | null>(null);
	let request = 0;

	const base = './';
	const worse = $derived(run ? worsenedJobIds(run, previous) : new Set<string>());

	function message(error: unknown): string {
		return error instanceof Error ? error.message : String(error);
	}

	async function selectRun(asOf: string) {
		if (!index) return;
		const entry = index.runs.find((r) => r.as_of === asOf);
		if (!entry) return;
		const ticket = ++request;
		selected = asOf;
		openJob = null;
		runLoading = true;
		const before = previousRunEntry(index, asOf);
		const [current, prior] = await Promise.allSettled([
			fetchRun(fetch, base, entry.file),
			before ? fetchRun(fetch, base, before.file) : Promise.resolve(null)
		]);
		if (ticket !== request) return; // a newer selection won
		if (current.status === 'fulfilled') {
			run = current.value;
			runError = null;
		} else {
			run = null;
			runError =
				current.reason instanceof RunFileError
					? current.reason.message
					: `${entry.file}: ${message(current.reason)}`;
		}
		previous = prior.status === 'fulfilled' ? prior.value : null;
		runLoading = false;
	}

	async function loadIndex(prefer: string | null = null) {
		try {
			index = await fetchIndex(fetch, base);
		} catch (error) {
			indexError = message(error);
			phase = 'index-error';
			return;
		}
		if (!index || index.runs.length === 0) {
			phase = 'empty';
			return;
		}
		const pick = index.runs.find((r) => r.as_of === prefer) ?? index.runs[0];
		await selectRun(pick.as_of);
		phase = 'ready';
	}

	onMount(async () => {
		const [health] = await Promise.all([fetchLiveHealth(fetch, base), loadIndex()]);
		live = health !== null;
	});

	async function closeLive() {
		showLive = false;
		await tick();
		runButton?.focus();
	}

	function open(jobId: string, trigger: HTMLElement) {
		const job = run?.jobs.find((j) => j.id === jobId);
		if (!job) return;
		returnFocus = trigger;
		openJob = job;
	}

	async function close() {
		openJob = null;
		await tick();
		returnFocus?.focus();
	}
</script>

<TopBar
	runs={index?.runs ?? []}
	{selected}
	sampleData={run?.source.sample_data ?? true}
	{live}
	onSelect={selectRun}
	onRun={() => (showLive = true)}
	bind:runButton
/>

<main class="page">
	{#if phase === 'loading' || (runLoading && !run && !runError)}
		<div class="skeleton" data-testid="loading" aria-busy="true" aria-label="Loading the latest run">
			<div class="row">
				{#each [0, 1, 2, 3] as i (i)}<div class="block tile"></div>{/each}
			</div>
			<div class="block summary"></div>
			<div class="block table"></div>
		</div>
	{:else if phase === 'empty'}
		<section class="card state" class:ready={live} data-testid="empty-state">
			{#if live}
				<h1>No runs yet. Ready for this morning's check.</h1>
				<p>
					Press <strong>Run this morning's check</strong> above. It reads the jobs, does the maths,
					checks every number in the AI's summary, saves the Excel report and drafts the email,
					one step at a time.
				</p>
				<p>It's a dry run on made-up sample data: nothing is sent.</p>
			{:else}
				<h1>No runs yet. Run <code>margin-watch run</code>.</h1>
				<p>Each morning run writes a file to <code>output/runs/</code>. Then <code>npm run sync-runs</code> copies it here.</p>
			{/if}
		</section>
	{:else if phase === 'index-error'}
		<section class="card state error" data-testid="run-error" role="alert">
			<h1>The run list couldn't be read</h1>
			<p class="num">{indexError}</p>
			<p>Re-run <code>margin-watch run</code> to rebuild <code>runs/index.json</code>.</p>
		</section>
	{:else if runError}
		<section class="card state error" data-testid="run-error" role="alert">
			<h1>This run couldn't be read</h1>
			<p class="num">{runError}</p>
			<p>Pick another run above, or re-run <code>margin-watch run</code> for this date.</p>
		</section>
	{:else if run}
		<h1 class="sr-only">Margin Watch for {run.as_of}</h1>
		<div class="stack">
			<KpiTiles {run} {previous} />
			<SummaryCard {run} onOpenJob={open} />
			<JobsSection jobs={run.jobs} {worse} onOpenJob={open} />
		</div>
		<p class="footnote">
			Sample data only: these jobs, clients and people are fictional. Nothing is connected to
			Simpro or Outlook. Source file: {run.source.name}.
		</p>
	{/if}
</main>

{#if showLive}
	<LiveRunPanel {base} onClose={closeLive} onFinished={(asOf) => loadIndex(asOf)} />
{/if}

{#if openJob}
	<JobDrawer job={openJob} onClose={close} />
{/if}

<style>
	.page {
		max-width: 1240px;
		margin: 0 auto;
		padding: 24px 24px 48px;
	}
	.stack {
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		gap: 16px;
	}
	.footnote {
		margin: 24px 0 0;
		font-size: 13px;
		color: var(--muted);
	}
	.state {
		padding: 32px;
		max-width: 640px;
	}
	.state h1 {
		margin: 0 0 8px;
		font-size: 18px;
	}
	.state p {
		margin: 0 0 4px;
		color: var(--muted);
	}
	.state.ready {
		max-width: 720px;
		border-color: var(--accent);
	}
	.state.ready p {
		color: var(--text);
		margin-bottom: 8px;
	}
	.state.error {
		border-color: var(--loss-border);
	}
	code {
		font-size: 0.92em;
		background: var(--surface-muted);
		border: 1px solid var(--border);
		border-radius: 4px;
		padding: 0 4px;
	}
	.skeleton {
		display: grid;
		gap: 16px;
	}
	.skeleton .row {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 16px;
	}
	.block {
		border-radius: var(--radius);
		background: var(--skeleton);
		animation: pulse 1.4s ease-in-out infinite;
	}
	.tile {
		height: 120px;
	}
	.summary {
		height: 180px;
	}
	.table {
		height: 420px;
	}
	@keyframes pulse {
		50% {
			opacity: 0.55;
		}
	}
	@media (max-width: 640px) {
		.page {
			padding: 16px 16px 40px;
		}
		.skeleton .row {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
