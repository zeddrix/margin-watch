import { formatMoney, formatShortDate, roundHalfUp } from './format';
import { severity } from './status';
import type { Run, RunIndex, RunIndexEntry } from './types';

export interface KpiLines {
	needingAction: string;
	dollarsAtRisk: string;
	averageMargin: string;
	toReview: string;
}

const FIRST_RUN = 'First run';

function countLine(current: number, previous: number, since: string): string {
	const delta = current - previous;
	if (delta === 0) return `No change ${since}`;
	return `${delta > 0 ? '+' : ''}${delta} ${since}`;
}

function moneyLine(current: number, previous: number, since: string): string {
	const delta = roundHalfUp(current, 0) - roundHalfUp(previous, 0);
	if (delta === 0) return `No change ${since}`;
	return `${delta > 0 ? '+' : '-'}${formatMoney(Math.abs(delta))} ${since}`;
}

function pointsLine(current: number | null, previous: number | null, since: string): string {
	if (current === null || previous === null) return `No comparable figure ${since}`;
	const delta = roundHalfUp(current - previous, 1);
	if (delta === 0) return `No change ${since}`;
	return `${delta > 0 ? '+' : ''}${delta.toFixed(1)} pts ${since}`;
}

/** One line of context per KPI tile, comparing with the previous run. */
export function sinceLines(current: Run, previous: Run | null): KpiLines {
	if (previous === null) {
		return {
			needingAction: FIRST_RUN,
			dollarsAtRisk: FIRST_RUN,
			averageMargin: FIRST_RUN,
			toReview: FIRST_RUN
		};
	}
	const since = `since ${formatShortDate(previous.as_of)}`;
	const now = current.portfolio;
	const before = previous.portfolio;
	return {
		needingAction: countLine(now.jobs_needing_action, before.jobs_needing_action, since),
		dollarsAtRisk: moneyLine(now.total_dollars_at_risk, before.total_dollars_at_risk, since),
		averageMargin: pointsLine(
			now.average_forecast_margin_pct,
			before.average_forecast_margin_pct,
			since
		),
		toReview: countLine(now.jobs_to_review, before.jobs_to_review, since)
	};
}

/** Job ids whose status got worse (ON_TRACK < WATCH < AT_RISK < LOSS). */
export function worsenedJobIds(current: Run, previous: Run | null): Set<string> {
	const worse = new Set<string>();
	if (previous === null) return worse;
	const before = new Map(previous.jobs.map((j) => [j.id, j.status]));
	for (const job of current.jobs) {
		const was = before.get(job.id);
		const now = severity(job.status);
		const then = was === undefined ? null : severity(was);
		if (now !== null && then !== null && now > then) worse.add(job.id);
	}
	return worse;
}

/** The newest run older than `asOf`. */
export function previousRunEntry(index: RunIndex, asOf: string): RunIndexEntry | null {
	const older = index.runs.filter((r) => r.as_of < asOf).sort((a, b) => (a.as_of < b.as_of ? 1 : -1));
	return older[0] ?? null;
}
