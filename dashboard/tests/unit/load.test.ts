import { describe, expect, it } from 'vitest';
import { RunFileError, parseIndex, parseRun } from '../../src/lib/load';
import { readFixture } from './fixtures';

describe('run file parsing', () => {
	it('AC-79 a fixture run and index parse', () => {
		const run = parseRun(readFixture('runs/2026-11-04.json'), '2026-11-04.json');
		const index = parseIndex(readFixture('runs/index.json'));

		expect(run.jobs).toHaveLength(14);
		expect(run.summary.provider).toBe('demo');
		expect(index.runs.map((r) => r.as_of)).toEqual(['2026-11-04', '2026-11-03']);
	});

	it('AC-79 broken run files raise RunFileError naming the file', () => {
		const good = readFixture('runs/2026-11-04.json') as Record<string, unknown>;
		const cases: unknown[] = [
			{ ...good, jobs: undefined },
			{ ...good, schema_version: 2 },
			'not an object',
			null
		];

		for (const value of cases) {
			expect(() => parseRun(value, '2026-11-04.json')).toThrow(RunFileError);
			expect(() => parseRun(value, '2026-11-04.json')).toThrow(/2026-11-04\.json/);
		}
	});

	it('AC-79 an index without a runs list raises RunFileError', () => {
		expect(() => parseIndex({ schema_version: 1 })).toThrow(RunFileError);
		expect(() => parseIndex({ schema_version: 1 })).toThrow(/index\.json/);
	});
});
