import type { Job, Status } from './types';

export type SortKey =
	| 'risk'
	| 'job'
	| 'client'
	| 'pm'
	| 'quoted'
	| 'forecast'
	| 'erosion'
	| 'at_risk'
	| 'driver';
export type SortDir = 'asc' | 'desc';

/** Jobs arrive in risk order; ties keep that order and missing figures always sort last. */
export function sortJobs(jobs: Job[], key: SortKey, dir: SortDir): Job[] {
	throw new Error(`not implemented: ${jobs.length} ${key} ${dir}`);
}

export function defaultDir(key: SortKey): SortDir {
	throw new Error(`not implemented: ${key}`);
}

export function filterJobs(jobs: Job[], status: Status | null, query: string): Job[] {
	throw new Error(`not implemented: ${jobs.length} ${status} ${query}`);
}

export function statusCounts(jobs: Job[]): Record<Status, number> {
	throw new Error(`not implemented: ${jobs.length}`);
}
