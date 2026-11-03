import { describe, expect, it } from 'vitest';
import { summaryItems } from '../../src/lib/summary';
import { fixtureRun } from './fixtures';

const rowText = (segments: { text: string }[]) => segments.map((s) => s.text).join('');
const linkIds = (items: ReturnType<typeof summaryItems>) =>
	items.flatMap((i) => i.segments.flatMap((s) => (s.kind === 'job' ? [s.jobId] : [])));

describe('summary reading rows', () => {
	it('AC-91 a single-paragraph AI summary becomes one row per sentence, toned by its first job', () => {
		const run = fixtureRun('2026-11-04');
		const items = summaryItems(run.summary.text, run.jobs);

		expect(items.map((i) => i.tone)).toEqual([
			'LOSS',
			'AT_RISK',
			'AT_RISK',
			'WATCH',
			'NEEDS_REVIEW',
			null
		]);
		expect(items.map((i) => rowText(i.segments)).join(' ')).toBe(run.summary.text);
		expect(rowText(items[0].segments)).toMatch(/^Dave Kowalski needs a call today.*-2\.5%.*17\.5%.*estimate\.$/);
		expect(rowText(items[5].segments)).toBe(
			'In total, 3 jobs need action today and forecast overruns add up to $66,300.'
		);
		expect(linkIds(items)).toEqual(['1042', '1038', '1035', '1033', '1040', '1039', '1044']);
	});

	it('AC-91 a multi-paragraph template summary keeps one row per paragraph', () => {
		const run = fixtureRun('2026-11-03');
		const items = summaryItems(run.summary.text, run.jobs);

		expect(items.map((i) => i.tone)).toEqual([null, 'LOSS', 'AT_RISK', 'WATCH']);
		expect(items.map((i) => rowText(i.segments)).join('\n\n')).toBe(run.summary.text);
		expect(linkIds(items)).toEqual(['1042', '1035', '1038', '1033', '1036', '1040', '1039', '1044']);
	});

	it('AC-91 decimals and amounts never split a sentence', () => {
		const run = fixtureRun('2026-11-04');
		const text = 'Margin is 17.5% today. It was $12,000.50 over. Call Dave.';

		expect(summaryItems(text, run.jobs).map((i) => rowText(i.segments))).toEqual([
			'Margin is 17.5% today.',
			'It was $12,000.50 over.',
			'Call Dave.'
		]);
	});
});
