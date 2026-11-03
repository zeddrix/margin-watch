import { describe, expect, it } from 'vitest';
import { bulletGeometry } from '../../src/lib/bullet';

describe('bullet chart geometry', () => {
	it('AC-77 an overrun: scale is the forecast, overrun segment from estimate to forecast', () => {
		expect(bulletGeometry({ estimate: 24000, forecast: 36000, actual: 21600 }, 300)).toEqual({
			scale: 36000,
			estimateWidth: 200,
			actualWidth: 180,
			forecastX: 300,
			overrunX: 200,
			overrunWidth: 100,
			over: true
		});
	});

	it('AC-77 on budget: no overrun segment', () => {
		const g = bulletGeometry({ estimate: 30000, forecast: 30000, actual: 12000 }, 300);

		expect(g.estimateWidth).toBe(300);
		expect(g.actualWidth).toBe(120);
		expect(g.forecastX).toBe(300);
		expect(g.overrunWidth).toBe(0);
		expect(g.over).toBe(false);
	});

	it('AC-77 complete under budget: marker inside the estimate bar', () => {
		const g = bulletGeometry({ estimate: 10000, forecast: 8000, actual: 8000 }, 300);

		expect(g.scale).toBe(10000);
		expect(g.forecastX).toBe(240);
		expect(g.overrunWidth).toBe(0);
		expect(g.over).toBe(false);
	});

	it('AC-77 no forecast (NEEDS_REVIEW) means no marker; all zero never divides by zero', () => {
		expect(bulletGeometry({ estimate: 30000, forecast: null, actual: 12000 }, 300).forecastX).toBe(
			null
		);
		expect(bulletGeometry({ estimate: 0, forecast: 0, actual: 0 }, 300)).toEqual({
			scale: 0,
			estimateWidth: 0,
			actualWidth: 0,
			forecastX: 0,
			overrunX: 0,
			overrunWidth: 0,
			over: false
		});
	});
});
