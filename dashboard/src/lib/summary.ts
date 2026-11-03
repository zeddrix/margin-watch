import type { Job, Provider, Summary } from './types';

export interface Badge {
	kind: 'verified' | 'rejected' | 'template';
	label: string;
}

export type Segment = { kind: 'text'; text: string } | { kind: 'job'; text: string; jobId: string };

const PROVIDER_NAMES: Record<Provider, string> = {
	demo: 'Demo AI',
	'demo-bad': 'Demo AI',
	local: 'Local model',
	claude: 'Claude',
	none: 'AI'
};

const FALLBACK_EXPLANATIONS: Record<string, string> = {
	no_api_key: 'No Claude API key is set, so the template summary was used.',
	unreachable: "The model couldn't be reached, so the template summary was used.",
	timeout: 'The model took too long to answer, so the template summary was used.',
	rate_limited: 'The model was busy (rate limited), so the template summary was used.',
	auth_error: 'The model rejected the API key, so the template summary was used.',
	api_error: 'The model returned an error, so the template summary was used.',
	refusal: 'The model declined to answer, so the template summary was used.',
	truncated: 'The model ran out of room mid-answer, so the template summary was used.',
	too_many_rounds: 'The model kept asking for data without answering, so the template was used.',
	empty_answer: 'The model gave an empty answer, so the template summary was used.',
	bad_response: 'The model sent a reply that could not be read, so the template was used.'
};

export function summaryBadge(summary: Summary): Badge {
	if (summary.source === 'ai_verified') {
		return { kind: 'verified', label: `${PROVIDER_NAMES[summary.provider]} · numbers verified` };
	}
	if (summary.rejected_tokens.length > 0) {
		return { kind: 'rejected', label: 'Template summary · AI answer rejected' };
	}
	return { kind: 'template', label: 'Template summary' };
}

/** Why the template was used, or null when there's nothing to explain (verified, or AI off). */
export function fallbackExplanation(summary: Summary): string | null {
	if (summary.source === 'ai_verified' || summary.fallback_reason === 'ai_off') return null;
	if (summary.rejected_tokens.length > 0) {
		const plural = summary.rejected_tokens.length > 1;
		return (
			`The AI answer included ${plural ? 'numbers' : 'a number'} the code never calculated, ` +
			'so it was thrown out and this template summary was used instead.'
		);
	}
	return FALLBACK_EXPLANATIONS[summary.fallback_reason ?? ''] ?? null;
}

/** Split `text` into text and job-link segments. Each job is linked once (tracked in `linked`). */
function linkSegments(text: string, flagged: Job[], linked: Set<string>): Segment[] {
	const hits: { start: number; end: number; job: Job }[] = [];
	for (const job of flagged) {
		if (linked.has(job.id)) continue;
		const start = text.indexOf(job.name);
		if (start >= 0) hits.push({ start, end: start + job.name.length, job });
	}
	hits.sort((a, b) => a.start - b.start || b.end - a.end);
	const segments: Segment[] = [];
	let cursor = 0;
	for (const hit of hits) {
		if (hit.start < cursor) continue;
		if (hit.start > cursor) segments.push({ kind: 'text', text: text.slice(cursor, hit.start) });
		segments.push({ kind: 'job', text: hit.job.name, jobId: hit.job.id });
		linked.add(hit.job.id);
		cursor = hit.end;
	}
	if (cursor < text.length) segments.push({ kind: 'text', text: text.slice(cursor) });
	return segments;
}

const flaggedJobs = (jobs: Job[]) => jobs.filter((j) => j.status !== 'ON_TRACK');

/** Paragraphs (split on blank lines) with each flagged job's name as a link segment. */
export function summaryParagraphs(text: string, jobs: Job[]): Segment[][] {
	const flagged = flaggedJobs(jobs);
	const linked = new Set<string>();
	return text.split('\n\n').map((paragraph) => linkSegments(paragraph, flagged, linked));
}

export interface SummaryItem {
	segments: Segment[];
	tone: Job['status'] | null;
}

/** A sentence ends at . ! or ? followed by whitespace, so "17.5%" and "$12,000.50" stay whole. */
function sentences(paragraph: string): string[] {
	return paragraph.split(/(?<=[.!?])\s+(?=\S)/);
}

/** Reading rows: one per paragraph, or one per sentence when the text is a single paragraph. */
export function summaryItems(text: string, jobs: Job[]): SummaryItem[] {
	const flagged = flaggedJobs(jobs);
	const status = new Map(jobs.map((j) => [j.id, j.status]));
	const paragraphs = text.split('\n\n');
	const chunks = paragraphs.length > 1 ? paragraphs : sentences(paragraphs[0]);
	const linked = new Set<string>();
	return chunks.map((chunk) => {
		const segments = linkSegments(chunk, flagged, linked);
		const first = segments.find((s) => s.kind === 'job');
		return { segments, tone: first?.kind === 'job' ? (status.get(first.jobId) ?? null) : null };
	});
}
