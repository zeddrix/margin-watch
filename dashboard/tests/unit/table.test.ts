import { describe, expect, it } from 'vitest';
import { defaultDir, filterJobs, sortJobs, statusCounts } from '../../src/lib/table';
import { fixtureRun } from './fixtures';

const jobs = fixtureRun('2026-11-04').jobs;
const ids = (list: { id: string }[]) => list.map((j) => j.id);
const RISK_ORDER = [
	'1042',
	'1038',
	'1035',
	'1033',
	'1040',
	'1039',
	'1044',
	'1037',
	'1031',
	'1032',
	'1034',
	'1036',
	'1041',
	'1043'
];

describe('sorting', () => {
	it('AC-74 dollars at risk descending, $0 jobs in risk order, missing figures last', () => {
		expect(ids(sortJobs(jobs, 'at_risk', 'desc'))).toEqual([
			'1038',
			'1042',
			'1035',
			'1033',
			'1037',
			'1040',
			'1031',
			'1032',
			'1034',
			'1036',
			'1041',
			'1043',
			'1039',
			'1044'
		]);
	});

	it('AC-74 ascending puts $0 jobs first and keeps missing figures last', () => {
		const sorted = ids(sortJobs(jobs, 'at_risk', 'asc'));

		expect(sorted.slice(0, 6)).toEqual(['1031', '1032', '1034', '1036', '1041', '1043']);
		expect(sorted.slice(-2)).toEqual(['1039', '1044']);
		expect(sorted[11]).toBe('1038');
	});

	it('AC-74 text columns sort alphabetically and risk restores the original order', () => {
		const byPm = sortJobs(jobs, 'pm', 'asc');

		expect(byPm[0].project_manager).toBe('Dave Kowalski');
		expect(ids(byPm.slice(0, 2))).toEqual(['1042', '1044']);
		expect(byPm.at(-1)?.project_manager).toBe('Tom Reilly');
		expect(ids(sortJobs(byPm, 'risk', 'asc'))).toEqual(RISK_ORDER);
		expect(ids(sortJobs(jobs, 'risk', 'asc'))).toEqual(RISK_ORDER);
		expect(jobs.map((j) => j.id)).toEqual(RISK_ORDER);
	});

	it('AC-74 money and erosion default to descending, text to ascending', () => {
		expect(defaultDir('at_risk')).toBe('desc');
		expect(defaultDir('erosion')).toBe('desc');
		expect(defaultDir('job')).toBe('asc');
		expect(defaultDir('risk')).toBe('asc');
	});
});

describe('filtering', () => {
	it('AC-75 status filter and search combine; search covers id, name and client', () => {
		expect(ids(filterJobs(jobs, 'AT_RISK', ''))).toEqual(['1038', '1035']);
		expect(ids(filterJobs(jobs, null, '  MEDICAL '))).toEqual(['1035']);
		expect(ids(filterJobs(jobs, 'AT_RISK', 'medical'))).toEqual(['1035']);
		expect(ids(filterJobs(jobs, 'LOSS', 'medical'))).toEqual([]);
		expect(ids(filterJobs(jobs, null, '1040'))).toEqual(['1040']);
		expect(ids(filterJobs(jobs, null, 'frostline'))).toEqual(['1042']);
		expect(filterJobs(jobs, null, '')).toHaveLength(14);
	});

	it('AC-75 status counts for the chips', () => {
		expect(statusCounts(jobs)).toEqual({
			LOSS: 1,
			AT_RISK: 2,
			WATCH: 2,
			NEEDS_REVIEW: 2,
			ON_TRACK: 7
		});
	});
});
