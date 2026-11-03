import { describe, expect, it } from 'vitest';
import { summaryBadge, summaryParagraphs } from '../../src/lib/summary';
import type { Summary } from '../../src/lib/types';
import { fixtureRun } from './fixtures';

const verified = (provider: Summary['provider']): Summary => ({
	text: 'x',
	source: 'ai_verified',
	provider,
	model: 'm',
	fallback_reason: null,
	rejected_tokens: []
});

describe('summary badge', () => {
	it('AC-78 verified badges name the provider; the demo is never called Claude', () => {
		expect(summaryBadge(verified('demo'))).toEqual({
			kind: 'verified',
			label: 'Demo AI · numbers verified'
		});
		expect(summaryBadge(verified('local')).label).toBe('Local model · numbers verified');
		expect(summaryBadge(verified('claude')).label).toBe('Claude · numbers verified');
		expect(summaryBadge(verified('demo')).label).not.toContain('Claude');
	});

	it('AC-78 rejected and plain template badges', () => {
		expect(summaryBadge(fixtureRun('2026-11-03').summary)).toEqual({
			kind: 'rejected',
			label: 'Template summary · AI answer rejected'
		});
		const off: Summary = {
			...verified('none'),
			source: 'template',
			fallback_reason: 'ai_off'
		};
		expect(summaryBadge(off)).toEqual({ kind: 'template', label: 'Template summary' });
	});
});

describe('summary links', () => {
	it('AC-78 paragraphs split on blank lines; flagged job names become links', () => {
		const run = fixtureRun('2026-11-03');
		const paragraphs = summaryParagraphs(run.summary.text, run.jobs);
		const links = paragraphs.flat().filter((s) => s.kind === 'job');

		expect(paragraphs).toHaveLength(run.summary.text.split('\n\n').length);
		expect(paragraphs.map((p) => p.map((s) => s.text).join(''))).toEqual(
			run.summary.text.split('\n\n')
		);
		expect(links.map((s) => (s.kind === 'job' ? s.jobId : ''))).toEqual([
			'1042',
			'1035',
			'1038',
			'1033',
			'1036',
			'1040',
			'1039',
			'1044'
		]);
		expect(links[0].text).toBe('Chiller replacement, cold-storage warehouse');
	});

	it('AC-78 ON_TRACK job names stay plain text', () => {
		const run = fixtureRun('2026-11-04');
		const text = 'Office tower AHU refurbishment is fine. Car park exhaust fans is on watch.';
		const segments = summaryParagraphs(text, run.jobs)[0];

		expect(segments).toEqual([
			{ kind: 'text', text: 'Office tower AHU refurbishment is fine. ' },
			{ kind: 'job', text: 'Car park exhaust fans', jobId: '1040' },
			{ kind: 'text', text: ' is on watch.' }
		]);
	});
});
