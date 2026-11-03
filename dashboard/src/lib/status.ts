import type { Status } from './types';

export type StatusIcon = 'loss' | 'risk' | 'watch' | 'review' | 'ok';

export interface StatusMeta {
	label: string;
	icon: StatusIcon;
	tone: string;
}

export const STATUS_ORDER: Status[] = ['LOSS', 'AT_RISK', 'WATCH', 'NEEDS_REVIEW', 'ON_TRACK'];

export function statusMeta(status: Status): StatusMeta {
	throw new Error(`not implemented: ${status}`);
}
