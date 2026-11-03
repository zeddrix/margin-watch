<script lang="ts">
	import { formatLongDate, formatRunStamp } from '../format';
	import type { RunIndexEntry } from '../types';

	let {
		runs,
		selected,
		sampleData,
		onSelect
	}: {
		runs: RunIndexEntry[];
		selected: string | null;
		sampleData: boolean;
		onSelect: (asOf: string) => void;
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
