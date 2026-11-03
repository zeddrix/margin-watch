// Display formatting, half-up like the Python side (agent/margin_watch/formatting.py).
// The numbers themselves were calculated by Python; this only rounds them for display.

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const DASH = '—';

/** Round half away from zero, without binary-float surprises (1.005 → 1.01) or "-0". */
export function roundHalfUp(value: number, decimals: number): number {
	const factor = 10 ** decimals;
	const scaled = Number((Math.abs(value) * factor).toPrecision(12));
	const rounded = Math.round(scaled) / factor;
	const signed = value < 0 ? -rounded : rounded;
	return signed === 0 ? 0 : signed;
}

export function formatMoney(value: number | null): string {
	if (value === null) return DASH;
	const rounded = roundHalfUp(value, 0);
	return `${rounded < 0 ? '-' : ''}$${Math.abs(rounded).toLocaleString('en-US')}`;
}

export function formatPct(value: number | null): string {
	return value === null ? DASH : `${roundHalfUp(value, 1).toFixed(1)}%`;
}

export function formatPts(value: number | null): string {
	return value === null ? DASH : `${roundHalfUp(value, 1).toFixed(1)} pts`;
}

function parseIsoDate(isoDate: string): Date {
	const [year, month, day] = isoDate.split('-').map(Number);
	return new Date(Date.UTC(year, month - 1, day));
}

export function formatShortDate(isoDate: string): string {
	const date = parseIsoDate(isoDate);
	return `${DAYS[date.getUTCDay()]} ${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}`;
}

export function formatLongDate(isoDate: string): string {
	return `${formatShortDate(isoDate)} ${parseIsoDate(isoDate).getUTCFullYear()}`;
}

const MELBOURNE = new Intl.DateTimeFormat('en-US', {
	timeZone: 'Australia/Melbourne',
	weekday: 'short',
	year: 'numeric',
	month: 'numeric',
	day: 'numeric',
	hour: 'numeric',
	minute: '2-digit',
	hour12: true
});

/** "Run Wed 4 Nov 2026, 6:30 AM Melbourne", always in Melbourne time. */
export function formatRunStamp(generatedAt: string): string {
	const parts = Object.fromEntries(
		MELBOURNE.formatToParts(new Date(generatedAt)).map((p) => [p.type, p.value])
	);
	const month = MONTHS[Number(parts.month) - 1];
	return `Run ${parts.weekday} ${parts.day} ${month} ${parts.year}, ${parts.hour}:${parts.minute} ${parts.dayPeriod.toUpperCase()} Melbourne`;
}
