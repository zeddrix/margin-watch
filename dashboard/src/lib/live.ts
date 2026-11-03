// The live dry run: health check, starting a run, and reading its NDJSON event stream.
import type { Status } from './types';

export interface LiveStep {
	id: string;
	title: string;
}

export interface NumberCheck {
	token: string;
	ok: boolean;
}

export type LiveEvent =
	| { type: 'start'; dry_run: boolean; ai: string; as_of: string; steps: LiveStep[] }
	| {
			type: 'step';
			step: string;
			state: 'running' | 'done' | 'warning';
			detail?: string;
			data?: {
				counts?: Record<Status, number>;
				dollars_at_risk?: string;
				jobs?: { id: string; name: string; problem: string }[];
				verified?: boolean;
				writer?: string;
				checks?: NumberCheck[];
				rejected?: string[];
				href?: string;
				file?: string;
				to?: string;
				subject?: string;
			};
	  }
	| { type: 'done'; as_of: string; sent: boolean; file: string }
	| { type: 'error'; step: string; message: string };

export class LiveStreamError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'LiveStreamError';
	}
}

function parseLine(line: string): LiveEvent {
	try {
		return JSON.parse(line) as LiveEvent;
	} catch {
		throw new LiveStreamError(`The live run sent a line that isn't JSON: ${line.slice(0, 80)}`);
	}
}

/** Turn streamed text chunks into events, even when a line is split across chunks. */
export async function* readEvents(
	chunks: Iterable<string> | AsyncIterable<string>
): AsyncGenerator<LiveEvent> {
	let buffer = '';
	for await (const chunk of chunks) {
		buffer += chunk;
		let newline = buffer.indexOf('\n');
		while (newline >= 0) {
			const line = buffer.slice(0, newline).trim();
			buffer = buffer.slice(newline + 1);
			if (line) yield parseLine(line);
			newline = buffer.indexOf('\n');
		}
	}
	if (buffer.trim()) yield parseLine(buffer.trim());
}

export interface LiveHealth {
	live: boolean;
	dry_run: boolean;
	sample_dates: string[];
}

type Fetch = (input: string, init?: RequestInit) => Promise<Response>;

/** The helper's health, or null on a static copy of the dashboard (no helper). */
export async function fetchLiveHealth(fetchFn: Fetch, base: string): Promise<LiveHealth | null> {
	try {
		const response = await fetchFn(`${base}api/health`);
		if (!response.ok) return null;
		const health = (await response.json()) as LiveHealth;
		return health.live ? health : null;
	} catch {
		return null; // no helper: the dashboard still works from its static run files
	}
}

async function* decode(body: ReadableStream<Uint8Array>): AsyncGenerator<string> {
	const reader = body.getReader();
	const decoder = new TextDecoder();
	for (;;) {
		const { done, value } = await reader.read();
		if (done) break;
		yield decoder.decode(value, { stream: true });
	}
	yield decoder.decode();
}

/** Start a live dry run and yield its events as they arrive. */
export async function* startLiveRun(
	fetchFn: Fetch,
	base: string,
	ai: 'demo' | 'demo-bad'
): AsyncGenerator<LiveEvent> {
	const response = await fetchFn(`${base}api/run`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ ai })
	});
	if (!response.ok || !response.body) {
		let message = `The helper answered HTTP ${response.status}.`;
		try {
			message = ((await response.json()) as { error?: string }).error ?? message;
		} catch {
			// keep the HTTP status message
		}
		throw new LiveStreamError(message);
	}
	yield* readEvents(decode(response.body));
}
