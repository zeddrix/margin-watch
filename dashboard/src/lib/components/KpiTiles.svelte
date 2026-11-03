<script lang="ts">
	import { sinceLines } from '../compare';
	import { formatMoney, formatPct } from '../format';
	import type { Run } from '../types';

	let { run, previous }: { run: Run; previous: Run | null } = $props();

	const lines = $derived(sinceLines(run, previous));
	const tiles = $derived([
		{
			id: 'kpi-action',
			label: 'Jobs needing action',
			hint: 'Loss or at risk',
			value: String(run.portfolio.jobs_needing_action),
			context: lines.needingAction,
			alert: run.portfolio.jobs_needing_action > 0
		},
		{
			id: 'kpi-risk',
			label: 'Dollars at risk',
			hint: 'Forecast overruns',
			value: formatMoney(run.portfolio.total_dollars_at_risk),
			context: lines.dollarsAtRisk,
			alert: false
		},
		{
			id: 'kpi-margin',
			label: 'Average forecast margin',
			hint: 'Weighted by sell price',
			value: formatPct(run.portfolio.average_forecast_margin_pct),
			context: lines.averageMargin,
			alert: false
		},
		{
			id: 'kpi-review',
			label: 'Jobs to review',
			hint: 'Data to check in Simpro',
			value: String(run.portfolio.jobs_to_review),
			context: lines.toReview,
			alert: false
		}
	]);
</script>

<section class="tiles" aria-label="Key figures">
	{#each tiles as tile (tile.id)}
		<div class="tile card" data-testid={tile.id}>
			<p class="label">{tile.label}</p>
			<p class="value num" class:alert={tile.alert} data-testid="kpi-value">{tile.value}</p>
			<p class="context num" data-testid="kpi-context">{tile.context}</p>
			<p class="hint">{tile.hint}</p>
		</div>
	{/each}
</section>

<style>
	.tiles {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 16px;
	}
	.tile {
		padding: 16px 20px;
		display: grid;
		gap: 2px;
	}
	.label {
		margin: 0;
		font-size: 13px;
		font-weight: 600;
		color: var(--muted);
	}
	.value {
		margin: 4px 0 0;
		font-size: 32px;
		font-weight: 700;
		line-height: 1.15;
		letter-spacing: -0.02em;
	}
	.value.alert {
		color: var(--loss-fg);
	}
	.context,
	.hint {
		margin: 0;
		font-size: 13px;
		color: var(--muted);
	}
	.context {
		color: var(--text);
	}
	@media (max-width: 900px) {
		.tiles {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
	@media (max-width: 640px) {
		.tiles {
			gap: 12px;
		}
		.tile {
			padding: 12px 16px;
		}
		.value {
			font-size: 26px;
		}
	}
</style>
