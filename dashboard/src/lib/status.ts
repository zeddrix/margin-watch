import type { Status } from './types';

export type StatusIcon = 'loss' | 'risk' | 'watch' | 'review' | 'ok';

export interface StatusMeta {
	label: string;
	icon: StatusIcon;
	tone: string;
}

export const STATUS_ORDER: Status[] = ['LOSS', 'AT_RISK', 'WATCH', 'NEEDS_REVIEW', 'ON_TRACK'];

const META: Record<Status, StatusMeta> = {
	LOSS: { label: 'LOSS', icon: 'loss', tone: 'loss' },
	AT_RISK: { label: 'AT RISK', icon: 'risk', tone: 'risk' },
	WATCH: { label: 'WATCH', icon: 'watch', tone: 'watch' },
	NEEDS_REVIEW: { label: 'NEEDS REVIEW', icon: 'review', tone: 'review' },
	ON_TRACK: { label: 'ON TRACK', icon: 'ok', tone: 'ok' }
};

/** Chip labels, in sentence case. */
export const STATUS_CHIP: Record<Status, string> = {
	LOSS: 'Loss',
	AT_RISK: 'At risk',
	WATCH: 'Watch',
	NEEDS_REVIEW: 'Needs review',
	ON_TRACK: 'On track'
};

export function statusMeta(status: Status): StatusMeta {
	return META[status];
}

/** How bad a status is, for "worse since last run". NEEDS_REVIEW isn't comparable. */
export function severity(status: Status): number | null {
	const order: Partial<Record<Status, number>> = { ON_TRACK: 0, WATCH: 1, AT_RISK: 2, LOSS: 3 };
	return order[status] ?? null;
}
