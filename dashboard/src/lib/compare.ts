import type { Run, RunIndex, RunIndexEntry } from './types';

export interface KpiLines {
	needingAction: string;
	dollarsAtRisk: string;
	averageMargin: string;
	toReview: string;
}

/** One line of context per KPI tile, comparing with the previous run. */
export function sinceLines(current: Run, previous: Run | null): KpiLines {
	throw new Error(`not implemented: ${current.as_of} ${previous?.as_of}`);
}

/** Job ids whose status got worse (ON_TRACK < WATCH < AT_RISK < LOSS). */
export function worsenedJobIds(current: Run, previous: Run | null): Set<string> {
	throw new Error(`not implemented: ${current.as_of} ${previous?.as_of}`);
}

export function previousRunEntry(index: RunIndex, asOf: string): RunIndexEntry | null {
	throw new Error(`not implemented: ${index.runs.length} ${asOf}`);
}
