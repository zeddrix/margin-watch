<script lang="ts">
	import { formatMoney, formatPct } from '../format';
	import { fallbackExplanation, summaryBadge, summaryParagraphs } from '../summary';
	import type { Run } from '../types';
	import StatusPill from './StatusPill.svelte';

	let {
		run,
		onOpenJob
	}: { run: Run; onOpenJob: (jobId: string, trigger: HTMLElement) => void } = $props();

	const badge = $derived(summaryBadge(run.summary));
	const paragraphs = $derived(summaryParagraphs(run.summary.text, run.jobs));
	const why = $derived(fallbackExplanation(run.summary));
	const calls = $derived(run.jobs.filter((j) => j.status === 'LOSS' || j.status === 'AT_RISK'));
</script>

<section class="card summary" data-testid="summary-card" aria-labelledby="summary-heading">
	<div class="head">
		<h2 id="summary-heading">Morning summary</h2>
		<span class="badge" data-kind={badge.kind} data-testid="summary-badge">
			<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14" focusable="false">
				{#if badge.kind === 'verified'}
					<path d="m3.5 8.3 2.8 2.8 6.2-6.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
				{:else if badge.kind === 'rejected'}
					<path d="M4.5 4.5l7 7M11.5 4.5l-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
				{:else}
					<path d="M4 5h8M4 8h8M4 11h5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
				{/if}
			</svg>
			{badge.label}
		</span>
	</div>
	<div class="layout">
	<aside class="calls" aria-labelledby="calls-heading">
		<h3 id="calls-heading">Call today</h3>
		{#if calls.length === 0}
			<p class="none">No calls needed today.</p>
		{:else}
			<ul>
				{#each calls as job (job.id)}
					<li>
						<button
							type="button"
							class="call"
							data-testid="call-{job.id}"
							onclick={(event) => onOpenJob(job.id, event.currentTarget)}
						>
							<span class="call-top">
								<StatusPill status={job.status} compact />
								<span class="call-money num">{formatMoney(job.dollars_at_risk)} at risk</span>
							</span>
							<span class="call-name"><span class="call-id num">{job.id}</span> {job.name}</span>
							<span class="call-meta num"
								>Call {job.project_manager} · forecast {formatPct(job.forecast_margin_pct)}</span
							>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</aside>
	<div class="text">
		{#each paragraphs as segments, i (i)}
			<p>
				{#each segments as segment, j (j)}{#if segment.kind === 'job'}<button
							type="button"
							class="job-link"
							data-testid="summary-link-{segment.jobId}"
							onclick={(event) => onOpenJob(segment.jobId, event.currentTarget)}
							>{segment.text}</button
						>{:else}{segment.text}{/if}{/each}
			</p>
		{/each}
	</div>
	</div>
	{#if why}
		<details class="why" data-testid="summary-why">
			<summary>Why?</summary>
			<div class="why-body" data-testid="summary-why-tokens">
				<p>{why}</p>
				{#if run.summary.rejected_tokens.length > 0}
					<p class="tokens">
						Rejected: {#each run.summary.rejected_tokens as token (token)}<code class="num"
								>{token}</code
							>{/each}
					</p>
				{/if}
			</div>
		</details>
	{/if}
	<p class="foot">
		Numbers come from the calculations, never from the AI. Every figure in an AI answer is checked
		against them before it is shown.
	</p>
</section>

<style>
	.summary {
		padding: 20px 24px;
	}
	.head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		flex-wrap: wrap;
		margin-bottom: 8px;
	}
	h2 {
		margin: 0;
		font-size: 15px;
		font-weight: 700;
	}
	.badge {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		font-weight: 600;
		border-radius: 999px;
		padding: 2px 12px 2px 10px;
		border: 1px solid var(--border-strong);
		color: var(--muted);
	}
	.badge[data-kind='verified'] {
		background: var(--ok-bg);
		border-color: var(--ok-border);
		color: var(--ok-fg);
	}
	.badge[data-kind='rejected'] {
		background: var(--risk-bg);
		border-color: var(--risk-border);
		color: var(--risk-fg);
	}
	.text {
		max-width: 70ch;
		font-size: 16.5px;
		line-height: 1.6;
	}
	.text p {
		margin: 0 0 10px;
	}
	.job-link {
		font: inherit;
		color: var(--accent);
		background: none;
		border: 0;
		padding: 0;
		text-decoration: underline;
		text-decoration-thickness: 1px;
		text-underline-offset: 3px;
		cursor: pointer;
		text-align: left;
	}
	.job-link:hover {
		color: var(--accent-hover);
		text-decoration-thickness: 2px;
	}
	.why {
		margin-top: 4px;
		font-size: 13px;
	}
	.layout {
		display: grid;
		grid-template-columns: minmax(0, 70ch) minmax(260px, 1fr);
		gap: 24px 32px;
		align-items: start;
	}
	.layout .text {
		grid-column: 1;
		grid-row: 1;
	}
	.calls {
		grid-column: 2;
		grid-row: 1;
		border-left: 1px solid var(--border);
		padding-left: 24px;
	}
	.calls h3 {
		margin: 0 0 8px;
		font-size: 13px;
		font-weight: 700;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.calls ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 8px;
	}
	.none {
		margin: 0;
		font-size: 13px;
		color: var(--muted);
	}
	.call {
		font: inherit;
		color: var(--text);
		text-align: left;
		width: 100%;
		display: grid;
		gap: 4px;
		padding: 10px 12px;
		border: 1px solid var(--border);
		border-radius: 8px;
		background: var(--surface);
		cursor: pointer;
		transition: border-color 150ms ease-out, background-color 150ms ease-out;
	}
	.call:hover {
		border-color: var(--accent);
		background: var(--surface-muted);
	}
	.call-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 8px;
	}
	.call-money {
		font-size: 13px;
		font-weight: 700;
	}
	.call-name {
		font-size: 15px;
		font-weight: 600;
		line-height: 1.35;
	}
	.call-id {
		color: var(--muted);
		font-weight: 400;
	}
	.call-meta {
		font-size: 13px;
		color: var(--muted);
	}
	.why summary {
		cursor: pointer;
		color: var(--accent);
		font-weight: 600;
		width: max-content;
	}
	.why-body {
		margin-top: 8px;
		padding: 12px 16px;
		border-radius: 8px;
		background: var(--surface-muted);
		border: 1px solid var(--border);
		max-width: 70ch;
	}
	.why-body p {
		margin: 0;
	}
	.tokens {
		margin-top: 8px !important;
	}
	code {
		font-size: 13px;
		background: var(--risk-bg);
		color: var(--risk-fg);
		border-radius: 4px;
		padding: 1px 6px;
		margin-left: 6px;
	}
	.foot {
		margin: 12px 0 0;
		font-size: 13px;
		color: var(--muted);
	}
	@media (max-width: 1023px) {
		.layout {
			grid-template-columns: minmax(0, 1fr);
		}
		.calls {
			grid-column: 1;
			grid-row: 1;
			border-left: 0;
			padding-left: 0;
		}
		.layout .text {
			grid-row: 2;
		}
	}
	@media (max-width: 640px) {
		.summary {
			padding: 16px;
		}
		.text {
			font-size: 16px;
		}
	}
</style>
