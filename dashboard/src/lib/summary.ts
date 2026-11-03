import type { Job, Summary } from './types';

export interface Badge {
	kind: 'verified' | 'rejected' | 'template';
	label: string;
}

export type Segment = { kind: 'text'; text: string } | { kind: 'job'; text: string; jobId: string };

export function summaryBadge(summary: Summary): Badge {
	throw new Error(`not implemented: ${summary.source}`);
}

/** Paragraphs (split on blank lines) with each flagged job's name as a link segment. */
export function summaryParagraphs(text: string, jobs: Job[]): Segment[][] {
	throw new Error(`not implemented: ${text.length} ${jobs.length}`);
}
