export interface BulletInput {
	estimate: number;
	forecast: number | null;
	actual: number;
}

export interface BulletGeometry {
	scale: number;
	estimateWidth: number;
	actualWidth: number;
	forecastX: number | null;
	overrunX: number;
	overrunWidth: number;
	over: boolean;
}

const px = (value: number) => Math.round(value * 100) / 100;

/** Pixel geometry for one cost centre: estimate bar, actual-to-date bar, forecast marker. */
export function bulletGeometry(input: BulletInput, width: number): BulletGeometry {
	const { estimate, forecast, actual } = input;
	const scale = Math.max(estimate, forecast ?? 0, actual, 0);
	const at = (value: number) => (scale === 0 ? 0 : px((value / scale) * width));
	const estimateWidth = at(estimate);
	const forecastX = forecast === null ? null : at(forecast);
	const over = forecast !== null && forecast > estimate;
	return {
		scale,
		estimateWidth,
		actualWidth: at(actual),
		forecastX,
		overrunX: estimateWidth,
		overrunWidth: over && forecastX !== null ? px(forecastX - estimateWidth) : 0,
		over
	};
}
