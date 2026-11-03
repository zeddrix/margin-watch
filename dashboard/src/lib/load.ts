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

const STATUSES = new Set(['LOSS', 'AT_RISK', 'WATCH', 'NEEDS_REVIEW', 'ON_TRACK']);

function isObject(value: unknown): value is Record<string, unknown> {
	return typeof value === 'object' && value !== null && !Array.isArray(value);
}

export function parseIndex(value: unknown): RunIndex {
	const file = 'index.json';
	if (!isObject(value)) throw new RunFileError(file, 'expected a JSON object');
	if (value.schema_version !== 1) throw new RunFileError(file, 'unsupported schema_version');
	if (!Array.isArray(value.runs)) throw new RunFileError(file, 'missing the `runs` list');
	for (const entry of value.runs) {
		if (!isObject(entry) || typeof entry.as_of !== 'string' || typeof entry.file !== 'string') {
			throw new RunFileError(file, 'every run needs `as_of` and `file`');
		}
	}
	return value as unknown as RunIndex;
}

export function parseRun(value: unknown, file: string): Run {
	if (!isObject(value)) throw new RunFileError(file, 'expected a JSON object');
	if (value.schema_version !== 1) throw new RunFileError(file, 'unsupported schema_version');
	if (typeof value.as_of !== 'string' || typeof value.generated_at !== 'string') {
		throw new RunFileError(file, 'missing `as_of` or `generated_at`');
	}
	if (!Array.isArray(value.jobs)) throw new RunFileError(file, 'missing the `jobs` list');
	if (!isObject(value.portfolio) || !isObject(value.counts) || !isObject(value.summary)) {
		throw new RunFileError(file, 'missing `portfolio`, `counts` or `summary`');
	}
	for (const job of value.jobs) {
		if (
			!isObject(job) ||
			typeof job.id !== 'string' ||
			!STATUSES.has(String(job.status)) ||
			!Array.isArray(job.cost_centres)
		) {
			throw new RunFileError(file, 'a job is missing its id, status or cost centres');
		}
	}
	return value as unknown as Run;
}

type Fetch = (input: string) => Promise<Response>;

/** The run index, or null when there isn't one yet (404). */
export async function fetchIndex(fetchFn: Fetch, base: string): Promise<RunIndex | null> {
	const response = await fetchFn(`${base}runs/index.json`);
	if (response.status === 404) return null;
	if (!response.ok) throw new RunFileError('index.json', `HTTP ${response.status}`);
	return parseIndex(await readJson(response, 'index.json'));
}

export async function fetchRun(fetchFn: Fetch, base: string, file: string): Promise<Run> {
	const response = await fetchFn(`${base}runs/${file}`);
	if (!response.ok) throw new RunFileError(file, `couldn't be loaded (HTTP ${response.status})`);
	return parseRun(await readJson(response, file), file);
}

async function readJson(response: Response, file: string): Promise<unknown> {
	try {
		return (await response.json()) as unknown;
	} catch {
		throw new RunFileError(file, "isn't valid JSON");
	}
}
