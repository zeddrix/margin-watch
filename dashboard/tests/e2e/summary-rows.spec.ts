import { expect, test } from '@playwright/test';
import { openDashboard } from './helpers';

test('AC-91 the summary reads as short toned rows and its links still open the drawer', async ({
	page
}) => {
	await openDashboard(page);
	const rows = page.getByTestId('summary-row');
	await expect(rows).toHaveCount(6);
	await expect(rows.first()).toHaveAttribute('data-tone', 'LOSS');
	await expect(rows.first()).toContainText('Dave Kowalski needs a call today');
	await expect(rows.last()).toHaveText(
		'In total, 3 jobs need action today and forecast overruns add up to $66,300.'
	);

	await rows.nth(1).getByTestId('summary-link-1038').click();

	await expect(page.getByRole('dialog').getByTestId('drawer-title')).toHaveText(
		'1038 Level 4 fit-out: VRF install'
	);
	await page.keyboard.press('Escape');
	await page.getByTestId('run-picker').selectOption('2026-11-03');
	await expect(rows).toHaveCount(4);
	await expect(rows.nth(1)).toHaveAttribute('data-tone', 'LOSS');
});
