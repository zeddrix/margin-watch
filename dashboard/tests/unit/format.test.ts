import { describe, expect, it } from 'vitest';
import {
	formatLongDate,
	formatMoney,
	formatPct,
	formatPts,
	formatRunStamp,
	formatShortDate
} from '../../src/lib/format';

describe('number formatting', () => {
	it('AC-71 money: whole dollars, half-up, minus before the $, dash for missing', () => {
		expect(formatMoney(16000)).toBe('$16,000');
		expect(formatMoney(-1250)).toBe('-$1,250');
		expect(formatMoney(12480.5)).toBe('$12,481');
		expect(formatMoney(12480.49)).toBe('$12,480');
		expect(formatMoney(0)).toBe('$0');
		expect(formatMoney(null)).toBe('—');
	});

	it('AC-71 percent and points: one decimal, half-up away from zero, never -0.0', () => {
		expect(formatPct(-2.5)).toBe('-2.5%');
		expect(formatPct(15.7394)).toBe('15.7%');
		expect(formatPct(-1.25)).toBe('-1.3%');
		expect(formatPct(6.25)).toBe('6.3%');
		expect(formatPct(-0.04)).toBe('0.0%');
		expect(formatPct(null)).toBe('—');
		expect(formatPts(20)).toBe('20.0 pts');
		expect(formatPts(18.75)).toBe('18.8 pts');
		expect(formatPts(null)).toBe('—');
	});
});

describe('dates', () => {
	it('AC-72 run stamp is shown in Melbourne time whatever the input offset', () => {
		expect(formatRunStamp('2026-11-04T06:30:00+11:00')).toBe(
			'Run Wed 4 Nov 2026, 6:30 AM Melbourne'
		);
		expect(formatRunStamp('2026-11-03T19:30:00Z')).toBe('Run Wed 4 Nov 2026, 6:30 AM Melbourne');
		expect(formatRunStamp('2026-11-04T14:05:00+11:00')).toBe(
			'Run Wed 4 Nov 2026, 2:05 PM Melbourne'
		);
	});

	it('AC-72 short and long dates from an ISO date', () => {
		expect(formatShortDate('2026-11-03')).toBe('Tue 3 Nov');
		expect(formatLongDate('2026-11-03')).toBe('Tue 3 Nov 2026');
		expect(formatLongDate('2026-11-04')).toBe('Wed 4 Nov 2026');
	});
});
