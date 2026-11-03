import type { Run, RunIndex } from './types';

export class RunFileError extends Error {
	constructor(
		public readonly file: string,
		message: string
	) {
		super(`${file}: ${message}`);
		this.name = 'RunFileError';
	}
}

export function parseIndex(value: unknown): RunIndex {
	throw new Error(`not implemented: ${typeof value}`);
}

export function parseRun(value: unknown, file: string): Run {
	throw new Error(`not implemented: ${typeof value} ${file}`);
}
