import { describe, expect, it } from 'vitest';
import { LiveStreamError, readEvents, type LiveEvent } from '../../src/lib/live';

async function collect(chunks: string[]): Promise<LiveEvent[]> {
	const events: LiveEvent[] = [];
	for await (const event of readEvents(chunks)) events.push(event);
	return events;
}

describe('reading the live stream', () => {
	it('AC-99 events split across chunks are reassembled and blank lines skipped', async () => {
		const events = await collect([
			'{"type":"step","step":"read","sta',
			'te":"running"}\n\n{"type":"step","step":"read","state":"done","detail":"Read 14 jobs."}\n{"ty',
			'pe":"done","as_of":"2026-11-04","sent":false,"file":"2026-11-04.json"}'
		]);

		expect(events).toEqual([
			{ type: 'step', step: 'read', state: 'running' },
			{ type: 'step', step: 'read', state: 'done', detail: 'Read 14 jobs.' },
			{ type: 'done', as_of: '2026-11-04', sent: false, file: '2026-11-04.json' }
		]);
	});

	it('AC-99 a line that is not JSON raises an error naming the line', async () => {
		const reading = collect(['{"type":"start"}\n', 'oops not json\n']);

		await expect(reading).rejects.toThrow(LiveStreamError);
		await expect(collect(['oops not json\n'])).rejects.toThrow(/oops not json/);
	});
});
