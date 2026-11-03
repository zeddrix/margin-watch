import { describe, expect, it } from 'vitest';
import { previousRunEntry, sinceLines, worsenedJobIds } from '../../src/lib/compare';
import { fixtureIndex, fixtureRun } from './fixtures';

const nov3 = fixtureRun('2026-11-03');
const nov4 = fixtureRun('2026-11-04');

describe('change since last run', () => {
	it('AC-76 KPI context lines for 4 Nov against 3 Nov', () => {
		expect(sinceLines(nov4, nov3)).toEqual({
			needingAction: '+1 since Tue 3 Nov',
			dollarsAtRisk: '+$7,500 since Tue 3 Nov',
			averageMargin: '-0.6 pts since Tue 3 Nov',
			toReview: 'No change since Tue 3 Nov'
		});
	});

	it('AC-76 every line says "First run" without a previous run', () => {
		expect(sinceLines(nov3, null)).toEqual({
			needingAction: 'First run',
			dollarsAtRisk: 'First run',
			averageMargin: 'First run',
			toReview: 'First run'
		});
	});

	it('AC-76 only jobs whose status got worse are marked', () => {
		expect([...worsenedJobIds(nov4, nov3)]).toEqual(['1038']);
		expect(worsenedJobIds(nov4, null).size).toBe(0);
		expect(worsenedJobIds(nov3, nov4).has('1036')).toBe(true);
	});

	it('AC-76 the previous run comes from the index', () => {
		const index = fixtureIndex();

		expect(previousRunEntry(index, '2026-11-04')?.as_of).toBe('2026-11-03');
		expect(previousRunEntry(index, '2026-11-03')).toBeNull();
	});
});
