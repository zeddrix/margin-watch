<script lang="ts">
	import { formatLongDate, formatRunStamp } from '../format';
	import type { RunIndexEntry } from '../types';

	let {
		runs,
		selected,
		sampleData,
		live = false,
		onSelect,
		onRun = () => {},
		runButton = $bindable(null)
	}: {
		runs: RunIndexEntry[];
		selected: string | null;
		sampleData: boolean;
		live?: boolean;
		onSelect: (asOf: string) => void;
		onRun?: () => void;
		runButton?: HTMLButtonElement | null;
	} = $props();

	const current = $derived(runs.find((r) => r.as_of === selected) ?? null);
</script>

<header class="topbar">
	<div class="inner">
		<div class="brand">
			<span class="mark" aria-hidden="true">
				<svg viewBox="0 0 20 20" width="20" height="20">
					<path d="M3 14.5 7.5 10l3 3L17 6.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
				</svg>
			</span>
			<span class="wordmark" data-testid="wordmark">Margin Watch</span>
			{#if sampleData}
				<span class="sample" data-testid="sample-pill">Sample data</span>
			{/if}
		</div>
		<div class="run">
			{#if live}
				<div class="live">
					<button type="button" class="run-button" data-testid="run-button" bind:this={runButton} onclick={onRun}>
						<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14"><path d="M4.5 3v10l8.5-5Z" fill="currentColor" /></svg>
						Run this morning's check
					</button>
					<span class="dry" data-testid="dry-run-pill">Dry run · nothing is sent</span>
				</div>
			{/if}
			{#if current}
				<span class="stamp num" data-testid="run-stamp">{formatRunStamp(current.generated_at)}</span>
			{/if}
			{#if runs.length > 0}
				<label class="picker">
					<span class="sr-only">Choose a run</span>
					<select
						data-testid="run-picker"
						value={selected}
						onchange={(event) => onSelect(event.currentTarget.value)}
					>
						{#each runs as run (run.as_of)}
							<option value={run.as_of}>{formatLongDate(run.as_of)}</option>
						{/each}
					</select>
				</label>
			{/if}
		</div>
	</div>
</header>

<style>
	.topbar {
		background: var(--surface);
		border-bottom: 1px solid var(--border);
	}
	.inner {
		max-width: 1240px;
		margin: 0 auto;
		padding: 12px 24px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		flex-wrap: wrap;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.mark {
		display: grid;
		place-items: center;
		width: 32px;
		height: 32px;
		border-radius: 8px;
		background: var(--accent);
		color: var(--surface);
	}
	.wordmark {
		font-size: 17px;
		font-weight: 700;
		letter-spacing: -0.01em;
	}
	.sample {
		font-size: 12px;
		font-weight: 600;
		color: var(--muted);
		border: 1px solid var(--border-strong);
		border-radius: 999px;
		padding: 1px 10px;
	}
	.run {
		display: flex;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
	}
.live {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
	}
	.run-button {
		font: inherit;
		font-size: 14px;
		font-weight: 700;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		padding: 8px 16px;
		border-radius: 8px;
		border: 1px solid var(--accent);
		background: var(--accent);
		color: var(--surface);
		cursor: pointer;
		box-shadow: 0 1px 2px rgb(15 23 42 / 0.12);
		transition: background-color 150ms ease-out, transform 150ms ease-out;
	}
	.run-button:hover {
		background: var(--accent-hover);
	}
	.run-button:active {
		transform: translateY(1px);
	}
	.dry {
		font-size: 12px;
		color: var(--muted);
	}
	.stamp {
		font-size: 13px;
		color: var(--muted);
	}
	select {
		font: inherit;
		font-size: 14px;
		color: var(--text);
		background: var(--surface);
		border: 1px solid var(--border-strong);
		border-radius: 8px;
		padding: 6px 32px 6px 12px;
		cursor: pointer;
	}
	@media (max-width: 640px) {
		.inner {
			padding: 12px 16px;
		}
		.run {
			width: 100%;
			justify-content: space-between;
		}
	}
</style>
