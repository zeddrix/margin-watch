<script lang="ts">
	import { bulletGeometry } from '../bullet';
	import { formatMoney, formatPct } from '../format';
	import type { CostCentre } from '../types';

	let { centre }: { centre: CostCentre } = $props();

	const WIDTH = 300;
	const geometry = $derived(
		bulletGeometry(
			{
				estimate: centre.estimated_cost ?? 0,
				forecast: centre.forecast_at_completion,
				actual: centre.actual_cost_to_date ?? 0
			},
			WIDTH
		)
	);
	const overrun = $derived(
		centre.overrun_pct === null || centre.overrun_dollars === null
			? null
			: `${centre.overrun_pct > 0 ? '+' : ''}${formatPct(centre.overrun_pct)}`
	);
	const description = $derived(
		centre.forecast_at_completion === null
			? `${centre.name}: estimate ${formatMoney(centre.estimated_cost)}, spent ${formatMoney(centre.actual_cost_to_date)} so far. No forecast.`
			: `${centre.name}: forecast ${formatMoney(centre.forecast_at_completion)} against a ${formatMoney(centre.estimated_cost)} estimate${overrun ? ` (${overrun})` : ''}; ${formatMoney(centre.actual_cost_to_date)} spent so far.`
	);
</script>

<figure class="bullet" data-testid="bullet-{centre.name}" class:over={geometry.over}>
	<figcaption>
		<span class="name">{centre.name}</span>
		{#if overrun}
			<span class="delta num" class:bad={geometry.over}>{overrun}</span>
		{/if}
	</figcaption>
	<svg viewBox="0 0 {WIDTH} 28" preserveAspectRatio="none" role="img" aria-label={description}>
		<rect class="estimate" x="0" y="6" width={geometry.estimateWidth} height="16" rx="3" />
		{#if geometry.overrunWidth > 0}
			<rect class="overrun" x={geometry.overrunX} y="6" width={geometry.overrunWidth} height="16" rx="3" />
		{/if}
		<rect class="actual" x="0" y="11" width={geometry.actualWidth} height="6" rx="2" />
		{#if geometry.forecastX !== null}
			<rect class="marker" x={Math.max(0, Math.min(WIDTH - 3, geometry.forecastX - 1.5))} y="1" width="3" height="26" rx="1" />
		{/if}
	</svg>
	<dl class="values num">
		<div><dt>Forecast</dt><dd>{formatMoney(centre.forecast_at_completion)}</dd></div>
		<div><dt>Estimate</dt><dd>{formatMoney(centre.estimated_cost)}</dd></div>
		<div><dt>Spent</dt><dd>{formatMoney(centre.actual_cost_to_date)}</dd></div>
	</dl>
</figure>

<style>
	.bullet {
		margin: 0;
		display: grid;
		gap: 6px;
	}
	figcaption {
		display: flex;
		justify-content: space-between;
		font-size: 14px;
	}
	.name {
		font-weight: 600;
	}
	.delta {
		color: var(--muted);
	}
	.delta.bad {
		color: var(--loss-fg);
		font-weight: 600;
	}
	svg {
		width: 100%;
		height: 28px;
		display: block;
	}
	.estimate {
		fill: var(--bar-estimate);
	}
	.overrun {
		fill: var(--loss-strong);
		opacity: 0.85;
	}
	.actual {
		fill: var(--bar-actual);
	}
	.marker {
		fill: var(--bar-marker);
	}
	.values {
		display: flex;
		gap: 16px;
		margin: 0;
		font-size: 13px;
	}
	.values div {
		display: flex;
		gap: 4px;
	}
	dt {
		color: var(--muted);
	}
	dd {
		margin: 0;
	}
</style>
