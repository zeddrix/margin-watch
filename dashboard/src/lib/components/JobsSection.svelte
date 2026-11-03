<script lang="ts">
	import { formatMoney, formatPct, formatPts } from '../format';
	import { STATUS_CHIP, STATUS_ORDER } from '../status';
	import { defaultDir, filterJobs, sortJobs, statusCounts, type SortDir, type SortKey } from '../table';
	import type { Job, Status } from '../types';
	import StatusPill from './StatusPill.svelte';

	let {
		jobs,
		worse,
		onOpenJob
	}: {
		jobs: Job[];
		worse: Set<string>;
		onOpenJob: (jobId: string, trigger: HTMLElement) => void;
	} = $props();

	let statusFilter = $state<Status | null>(null);
	let query = $state('');
	let sortKey = $state<SortKey>('risk');
	let sortDir = $state<SortDir>('asc');

	const counts = $derived(statusCounts(jobs));
	const visible = $derived(sortJobs(filterJobs(jobs, statusFilter, query), sortKey, sortDir));

	const columns: { key: SortKey; label: string; numeric: boolean }[] = [
		{ key: 'risk', label: 'Status', numeric: false },
		{ key: 'job', label: 'Job', numeric: false },
		{ key: 'client', label: 'Client', numeric: false },
		{ key: 'pm', label: 'PM', numeric: false },
		{ key: 'quoted', label: 'Quoted %', numeric: true },
		{ key: 'forecast', label: 'Forecast %', numeric: true },
		{ key: 'erosion', label: 'Erosion', numeric: true },
		{ key: 'at_risk', label: '$ at risk', numeric: true },
		{ key: 'driver', label: 'Main driver', numeric: false }
	];

	function sortBy(key: SortKey) {
		if (key === sortKey && key !== 'risk') {
			sortDir = sortDir === 'asc' ? 'desc' : 'asc';
		} else {
			sortKey = key;
			sortDir = defaultDir(key);
		}
	}

	function ariaSort(key: SortKey): 'ascending' | 'descending' | 'none' {
		if (key !== sortKey) return 'none';
		return sortDir === 'asc' ? 'ascending' : 'descending';
	}

	function onRowKey(event: KeyboardEvent, job: Job) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			onOpenJob(job.id, event.currentTarget as HTMLElement);
		}
	}
</script>

<section class="card jobs" aria-labelledby="jobs-heading">
	<div class="toolbar">
		<div class="title-row">
			<h2 id="jobs-heading">Jobs</h2>
			<p class="count num" data-testid="job-count" aria-live="polite">
				{visible.length} of {jobs.length} jobs
			</p>
		</div>
		<div class="controls">
			<div class="chips" role="group" aria-label="Filter by status">
				<button
					type="button"
					class="chip"
					data-testid="chip-all"
					aria-pressed={statusFilter === null}
					onclick={() => (statusFilter = null)}
				>
					All <span class="chip-count num">{jobs.length}</span>
				</button>
				{#each STATUS_ORDER as status (status)}
					<button
						type="button"
						class="chip"
						data-tone={status}
						data-testid="chip-{status}"
						aria-pressed={statusFilter === status}
						onclick={() => (statusFilter = status)}
					>
						<span class="dot" aria-hidden="true"></span>{STATUS_CHIP[status]}
						<span class="chip-count num">{counts[status]}</span>
					</button>
				{/each}
			</div>
			<label class="search">
				<span class="sr-only">Search by job or client</span>
				<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14">
					<circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6" />
					<path d="m10.5 10.5 3 3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
				</svg>
				<input
					type="search"
					placeholder="Search job or client"
					data-testid="job-search"
					bind:value={query}
				/>
			</label>
		</div>
	</div>

	<div class="table-wrap">
		<table data-testid="jobs-table">
			<caption class="sr-only">
				Jobs, worst first. Select a row to see why it is flagged.
			</caption>
			<thead>
				<tr>
					{#each columns as column (column.key)}
						<th
							scope="col"
							class:numeric={column.numeric}
							aria-sort={ariaSort(column.key)}
							data-testid="col-{column.key}"
						>
							<button type="button" data-testid="sort-{column.key}" onclick={() => sortBy(column.key)}>
								{column.label}
								<svg class="sort-icon" class:active={column.key === sortKey} aria-hidden="true" viewBox="0 0 10 14" width="8" height="12">
									<path d="M5 1 9 5H1Z" fill="currentColor" opacity={ariaSort(column.key) === 'ascending' ? 1 : 0.35} />
									<path d="M5 13 1 9h8Z" fill="currentColor" opacity={ariaSort(column.key) === 'descending' ? 1 : 0.35} />
								</svg>
							</button>
						</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each visible as job (job.id)}
					<tr
						data-job-id={job.id}
						data-testid="job-row-{job.id}"
						tabindex="0"
						aria-label="{job.id} {job.name}, {STATUS_CHIP[job.status]}. Open details."
						onclick={(event) => onOpenJob(job.id, event.currentTarget)}
						onkeydown={(event) => onRowKey(event, job)}
					>
						<td class="status-cell">
							<StatusPill status={job.status} />
							{#if worse.has(job.id)}
								<span class="worse" data-testid="worse-{job.id}">↑ worse since last run</span>
							{/if}
						</td>
						<td class="job-cell">
							<span class="job-id num">{job.id}</span>
							<span class="job-name">{job.name}</span>
						</td>
						<td>{job.client}</td>
						<td class="pm">{job.project_manager}</td>
						<td class="numeric num">{formatPct(job.quoted_margin_pct)}</td>
						<td class="numeric num">{formatPct(job.forecast_margin_pct)}</td>
						<td class="numeric num">{formatPts(job.margin_erosion_pts)}</td>
						<td class="numeric num strong">{formatMoney(job.dollars_at_risk)}</td>
						<td>{job.main_driver ?? '—'}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<ul class="cards" data-testid="job-cards" aria-label="Jobs, worst first">
		{#each visible as job (job.id)}
			<li>
				<button
					type="button"
					class="job-card"
					data-job-id={job.id}
					data-testid="job-card-{job.id}"
					onclick={(event) => onOpenJob(job.id, event.currentTarget)}
				>
					<span class="card-top">
						<StatusPill status={job.status} compact />
						{#if worse.has(job.id)}
							<span class="worse" data-testid="card-worse-{job.id}">↑ worse</span>
						{/if}
					</span>
					<span class="card-name"><span class="job-id num">{job.id}</span> {job.name}</span>
					<span class="card-figures num">
						<span><span class="fig-label">At risk</span> {formatMoney(job.dollars_at_risk)}</span>
						<span><span class="fig-label">Forecast</span> {formatPct(job.forecast_margin_pct)}</span>
					</span>
				</button>
			</li>
		{/each}
	</ul>

	{#if visible.length === 0}
		<p class="no-match">No jobs match. Clear the search or choose “All”.</p>
	{/if}
</section>

<style>
	.jobs {
		padding: 0;
	}
	.toolbar {
		padding: 16px 24px;
		display: grid;
		gap: 12px;
		border-bottom: 1px solid var(--border);
	}
	.title-row {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
	}
	h2 {
		margin: 0;
		font-size: 15px;
		font-weight: 700;
	}
	.count {
		margin: 0;
		font-size: 13px;
		color: var(--muted);
	}
	.controls {
		display: flex;
		gap: 12px;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
	}
	.chips {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}
	.chip {
		font: inherit;
		font-size: 13px;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 12px;
		border-radius: 999px;
		border: 1px solid var(--border-strong);
		background: var(--surface);
		color: var(--text);
		cursor: pointer;
		transition: background-color 160ms ease-out, border-color 160ms ease-out;
	}
	.chip:hover {
		border-color: var(--accent);
	}
	.chip[aria-pressed='true'] {
		background: var(--accent-soft);
		border-color: var(--accent);
		font-weight: 600;
	}
	.chip-count {
		color: var(--muted);
	}
	.chip[aria-pressed='true'] .chip-count {
		color: var(--text);
	}
	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--dot);
		border: 1px solid var(--dot-border, transparent);
	}
	.chip[data-tone='LOSS'] {
		--dot: var(--loss-fg);
	}
	.chip[data-tone='AT_RISK'] {
		--dot: var(--risk-fg);
	}
	.chip[data-tone='WATCH'] {
		--dot: var(--watch-fg);
	}
	.chip[data-tone='NEEDS_REVIEW'] {
		--dot: var(--review-fg);
	}
	.chip[data-tone='ON_TRACK'] {
		--dot: var(--ok-fg);
	}
	.search {
		display: flex;
		align-items: center;
		gap: 8px;
		border: 1px solid var(--border-strong);
		border-radius: 8px;
		padding: 0 12px;
		color: var(--muted);
		background: var(--surface);
		min-width: 240px;
	}
	.search:focus-within {
		outline: 2px solid var(--focus);
		outline-offset: 2px;
	}
	.search input {
		font: inherit;
		font-size: 14px;
		border: 0;
		outline: none;
		background: transparent;
		color: var(--text);
		padding: 6px 0;
		width: 100%;
	}
	.table-wrap {
		overflow: visible;
	}
	table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
		font-size: 14px;
	}
	th {
		position: sticky;
		top: 0;
		z-index: 1;
		background: var(--surface-muted);
		border-bottom: 1px solid var(--border);
		text-align: left;
		padding: 0;
		white-space: nowrap;
	}
	th button {
		font: inherit;
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
		background: none;
		border: 0;
		cursor: pointer;
		width: 100%;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 10px 12px;
	}
	th.numeric button {
		justify-content: flex-end;
	}
	th button:hover {
		color: var(--text);
	}
	th[aria-sort='ascending'] button,
	th[aria-sort='descending'] button {
		color: var(--text);
	}
	.sort-icon {
		flex: none;
	}
	th:first-child button,
	td:first-child {
		padding-left: 24px;
	}
	th:last-child button,
	td:last-child {
		padding-right: 24px;
	}
	td {
		padding: 10px 12px;
		border-bottom: 1px solid var(--border);
		vertical-align: middle;
	}
	tbody tr {
		cursor: pointer;
		transition: background-color 150ms ease-out;
	}
	tbody tr:hover {
		background: var(--surface-muted);
	}
	tbody tr:focus-visible {
		outline: 2px solid var(--focus);
		outline-offset: -2px;
		border-radius: 0;
	}
	tbody tr:last-child td {
		border-bottom: 0;
	}
	.numeric {
		text-align: right;
		white-space: nowrap;
	}
	.strong {
		font-weight: 600;
	}
	.status-cell {
		white-space: nowrap;
	}
	.worse {
		display: block;
		margin-top: 4px;
		font-size: 12px;
		font-weight: 600;
		color: var(--loss-fg);
	}
	.job-cell {
		min-width: 220px;
	}
	.job-id {
		color: var(--muted);
		margin-right: 6px;
	}
	.job-name {
		font-weight: 600;
	}
	.pm {
		white-space: nowrap;
	}
	.cards {
		display: none;
		list-style: none;
		margin: 0;
		padding: 8px 16px 16px;
	}
	.no-match {
		margin: 0;
		padding: 16px 24px 20px;
		color: var(--muted);
		font-size: 14px;
	}
	@media (max-width: 1100px) {
		.table-wrap {
			overflow-x: auto;
		}
		table {
			font-size: 13px;
		}
		.job-cell {
			min-width: 160px;
		}
		.pm {
			white-space: normal;
		}
		td,
		th button {
			padding-left: 8px;
			padding-right: 8px;
		}
	}
	@media (max-width: 640px) {
		.toolbar {
			padding: 16px;
		}
		.search {
			min-width: 0;
			width: 100%;
		}
		.table-wrap {
			display: none;
		}
		.cards {
			display: grid;
			gap: 8px;
		}
		.job-card {
			font: inherit;
			color: var(--text);
			text-align: left;
			width: 100%;
			display: grid;
			gap: 6px;
			padding: 12px 14px;
			border: 1px solid var(--border);
			border-radius: 10px;
			background: var(--surface);
			cursor: pointer;
		}
		.job-card:active {
			background: var(--surface-muted);
		}
		.card-top {
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 8px;
		}
		.card-top .worse {
			margin: 0;
		}
		.card-name {
			font-weight: 600;
			font-size: 15px;
			line-height: 1.35;
		}
		.card-figures {
			display: flex;
			gap: 16px;
			font-size: 14px;
		}
		.fig-label {
			color: var(--muted);
			font-size: 12px;
			margin-right: 4px;
		}
	}
</style>
