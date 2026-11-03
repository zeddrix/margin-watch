import { expect, test } from '@playwright/test';
import { openDashboard } from './helpers';

test('AC-83 drawer opens by mouse with the job details, closes on Esc and backdrop', async ({
	page
}) => {
	await openDashboard(page);
	const row = page.getByTestId('job-row-1042');

	await row.click();

	const drawer = page.getByRole('dialog');
	await expect(drawer).toBeVisible();
	await expect(drawer.getByTestId('drawer-title')).toHaveText(
		'1042 Chiller replacement, cold-storage warehouse'
	);
	await expect(drawer).toContainText('Frostline Logistics');
	await expect(drawer).toContainText('Frostline cold store, Dandenong South');
	await expect(drawer).toContainText('Dave Kowalski');
	await expect(drawer.getByTestId('drawer-status')).toHaveText(/LOSS/);
	await expect(drawer.getByTestId('drawer-why')).toHaveText(
		'Heading for a loss: forecast margin -2.5% against 17.5% quoted. Main driver: Labour, projected $12,000 (50.0%) over estimate.'
	);
	await expect(drawer.getByTestId('drawer-quoted')).toHaveText('17.5%');
	await expect(drawer.getByTestId('drawer-forecast')).toHaveText('-2.5%');
	await expect(drawer.getByTestId('drawer-erosion')).toHaveText('20.0 pts');
	await expect(drawer.getByTestId('drawer-at-risk')).toHaveText('$16,000');
	await expect(drawer.locator('[data-testid^="bullet-"]')).toHaveCount(4);
	await expect(drawer.getByTestId('bullet-Labour')).toContainText('$36,000');
	await expect(drawer.getByTestId('bullet-Labour')).toContainText('$24,000');
	await expect(drawer.getByTestId('bullet-Labour')).toContainText('+50.0%');

	await page.keyboard.press('Escape');

	await expect(drawer).toBeHidden();
	await expect(row).toBeFocused();

	await row.click();
	await expect(page.getByRole('dialog')).toBeVisible();
	await page.getByTestId('drawer-backdrop').click({ position: { x: 20, y: 300 } });

	await expect(page.getByRole('dialog')).toBeHidden();
});

test('AC-84 drawer opens with Enter, traps focus, Esc returns focus to the row', async ({
	page
}) => {
	await openDashboard(page);
	const row = page.getByTestId('job-row-1038');
	await row.focus();

	await page.keyboard.press('Enter');

	const drawer = page.getByRole('dialog');
	await expect(drawer.getByTestId('drawer-title')).toHaveText('1038 Level 4 fit-out: VRF install');
	await expect
		.poll(() => drawer.evaluate((el) => el.contains(document.activeElement)))
		.toBe(true);
	for (let i = 0; i < 8; i += 1) {
		await page.keyboard.press('Tab');
		expect(await drawer.evaluate((el) => el.contains(document.activeElement))).toBe(true);
	}
	await page.keyboard.press('Shift+Tab');
	expect(await drawer.evaluate((el) => el.contains(document.activeElement))).toBe(true);

	await page.keyboard.press('Escape');

	await expect(drawer).toBeHidden();
	await expect(row).toBeFocused();
});

test('AC-85 NEEDS_REVIEW drawers show the data problem and what to check in Simpro', async ({
	page
}) => {
	await openDashboard(page);

	await page.getByTestId('job-row-1039').click();

	const drawer = page.getByRole('dialog');
	await expect(drawer.getByTestId('drawer-review')).toContainText(
		"Percent complete is missing, so the forecast can't be worked out."
	);
	await expect(drawer.getByTestId('drawer-check')).toContainText('What to check in Simpro');
	await expect(drawer.getByTestId('drawer-check')).toContainText('percent complete');
	await expect(drawer.getByTestId('drawer-quoted')).toHaveCount(0);

	await page.keyboard.press('Escape');
	await page.getByTestId('job-row-1044').click();

	await expect(page.getByRole('dialog').getByTestId('drawer-review')).toContainText(
		'Materials actual cost to date is negative (-$1,250).'
	);
});
