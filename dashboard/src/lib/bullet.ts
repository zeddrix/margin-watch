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

export function bulletGeometry(input: BulletInput, width: number): BulletGeometry {
	throw new Error(`not implemented: ${input.estimate} ${width}`);
}
