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

/** Turn streamed text chunks into events, even when a line is split across chunks. */
export async function* readEvents(
	chunks: Iterable<string> | AsyncIterable<string>
): AsyncGenerator<LiveEvent> {
	throw new LiveStreamError(`not implemented: ${typeof chunks}`);
	yield* [];
}
