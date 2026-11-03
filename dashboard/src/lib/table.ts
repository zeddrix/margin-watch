import { STATUS_ORDER } from './status';
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

type Value = string | number | null;

const VALUE: Record<Exclude<SortKey, 'risk'>, (job: Job) => Value> = {
	job: (j) => j.name,
	client: (j) => j.client,
	pm: (j) => j.project_manager,
	quoted: (j) => j.quoted_margin_pct,
	forecast: (j) => j.forecast_margin_pct,
	erosion: (j) => j.margin_erosion_pts,
	at_risk: (j) => j.dollars_at_risk,
	driver: (j) => j.main_driver
};

/** Risk order, the same rule as the agent: status, then dollars at risk descending, then id. */
export function riskCompare(a: Job, b: Job): number {
	const byStatus = STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status);
	if (byStatus !== 0) return byStatus;
	const byMoney = (b.dollars_at_risk ?? 0) - (a.dollars_at_risk ?? 0);
	if (byMoney !== 0) return byMoney;
	return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
}

/** Ties keep risk order, and missing figures (NEEDS_REVIEW) always sort last. */
export function sortJobs(jobs: Job[], key: SortKey, dir: SortDir): Job[] {
	const sorted = [...jobs];
	if (key === 'risk') return sorted.sort(riskCompare);
	const value = VALUE[key];
	const sign = dir === 'asc' ? 1 : -1;
	return sorted.sort((a, b) => {
		const x = value(a);
		const y = value(b);
		if (x === null || y === null) {
			if (x === y) return riskCompare(a, b);
			return x === null ? 1 : -1;
		}
		const order =
			typeof x === 'number' && typeof y === 'number'
				? x - y
				: String(x).localeCompare(String(y), 'en');
		return order === 0 ? riskCompare(a, b) : sign * order;
	});
}

export function defaultDir(key: SortKey): SortDir {
	return key === 'at_risk' || key === 'erosion' ? 'desc' : 'asc';
}

export function filterJobs(jobs: Job[], status: Status | null, query: string): Job[] {
	const needle = query.trim().toLowerCase();
	return jobs.filter(
		(job) =>
			(status === null || job.status === status) &&
			(needle === '' ||
				[job.id, job.name, job.client].some((field) => field.toLowerCase().includes(needle)))
	);
}

export function statusCounts(jobs: Job[]): Record<Status, number> {
	const counts = Object.fromEntries(STATUS_ORDER.map((s) => [s, 0])) as Record<Status, number>;
	for (const job of jobs) counts[job.status] += 1;
	return counts;
}
