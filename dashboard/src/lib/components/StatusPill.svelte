<script lang="ts">
	import { statusMeta } from '../status';
	import type { Status } from '../types';

	let { status, compact = false }: { status: Status; compact?: boolean } = $props();
	const meta = $derived(statusMeta(status));
</script>

<!-- Icon + word + colour: status is never shown by colour alone. -->
<span class="pill" class:compact data-tone={meta.tone}>
	<svg aria-hidden="true" viewBox="0 0 16 16" width="14" height="14" focusable="false">
		{#if meta.icon === 'loss'}
			<circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.6" />
			<path d="M8 4.5v5M5.5 7.5 8 10l2.5-2.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
		{:else if meta.icon === 'risk'}
			<path d="M8 1.8 14.6 13.5H1.4Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
			<path d="M8 6v3.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
			<circle cx="8" cy="11.6" r="0.9" fill="currentColor" />
		{:else if meta.icon === 'watch'}
			<path d="M1.3 8S3.8 3.5 8 3.5 14.7 8 14.7 8 12.2 12.5 8 12.5 1.3 8 1.3 8Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
			<circle cx="8" cy="8" r="2" fill="currentColor" />
		{:else if meta.icon === 'review'}
			<circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.6" />
			<path d="M6.2 6.3a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.1v.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
			<circle cx="8" cy="11.7" r="0.85" fill="currentColor" />
		{:else}
			<circle cx="8" cy="8" r="6.5" fill="none" stroke="currentColor" stroke-width="1.6" />
			<path d="m5.2 8.2 1.9 1.9 3.8-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
		{/if}
	</svg>
	<span>{meta.label}</span>
</span>

<style>
	.pill {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 2px 10px 2px 8px;
		border-radius: 999px;
		border: 1px solid var(--tone-border);
		background: var(--tone-bg);
		color: var(--tone-fg);
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.02em;
		line-height: 20px;
		white-space: nowrap;
	}
	.pill.compact {
		padding: 0 8px 0 6px;
		font-size: 11px;
	}
	svg {
		flex: none;
	}
	[data-tone='loss'] {
		--tone-bg: var(--loss-bg);
		--tone-fg: var(--loss-fg);
		--tone-border: var(--loss-border);
	}
	[data-tone='risk'] {
		--tone-bg: var(--risk-bg);
		--tone-fg: var(--risk-fg);
		--tone-border: var(--risk-border);
	}
	[data-tone='watch'] {
		--tone-bg: var(--watch-bg);
		--tone-fg: var(--watch-fg);
		--tone-border: var(--watch-border);
	}
	[data-tone='review'] {
		--tone-bg: var(--review-bg);
		--tone-fg: var(--review-fg);
		--tone-border: var(--review-border);
	}
	[data-tone='ok'] {
		--tone-bg: var(--ok-bg);
		--tone-fg: var(--ok-fg);
		--tone-border: var(--ok-border);
	}
</style>
