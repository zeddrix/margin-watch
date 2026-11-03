import { describe, expect, it } from 'vitest';
import { render } from 'svelte/server';
import StatusPill from '../../src/lib/components/StatusPill.svelte';
import { STATUS_ORDER, statusMeta } from '../../src/lib/status';

describe('status pill', () => {
	it('AC-73 every status has its own word, icon and tone', () => {
		expect(STATUS_ORDER.map((s) => statusMeta(s).label)).toEqual([
			'LOSS',
			'AT RISK',
			'WATCH',
			'NEEDS REVIEW',
			'ON TRACK'
		]);
		const icons = new Set(STATUS_ORDER.map((s) => statusMeta(s).icon));
		const tones = new Set(STATUS_ORDER.map((s) => statusMeta(s).tone));
		expect(icons.size).toBe(5);
		expect(tones.size).toBe(5);
	});

	it('AC-73 the rendered pill shows the word as text next to an aria-hidden icon', () => {
		const { body } = render(StatusPill, { props: { status: 'AT_RISK' } });

		expect(body).toContain('AT RISK');
		expect(body).toMatch(/<svg[^>]*aria-hidden="true"/);
		expect(body).toContain(`data-tone="${statusMeta('AT_RISK').tone}"`);
	});
});
