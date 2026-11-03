import { expect, test } from '@playwright/test';
import { RISK_ORDER_4_NOV, openDashboard } from './helpers';

test.use({ viewport: { width: 390, height: 844 }, hasTouch: true });

test('AC-89 at 390px jobs are stacked cards and the drawer still works', async ({ page }) => {
	await openDashboard(page);
	const cards = page.getByTestId('job-cards');
	await expect(cards).toBeVisible();
	await expect(page.getByTestId('jobs-table')).toBeHidden();

	const ids = await cards
		.locator('[data-job-id]')
		.evaluateAll((els) => els.map((e) => e.getAttribute('data-job-id')));
	expect(ids).toEqual(RISK_ORDER_4_NOV);
	const card = page.getByTestId('job-card-1042');
	await expect(card).toContainText('LOSS');
	await expect(card).toContainText('Chiller replacement, cold-storage warehouse');
	await expect(card).toContainText('$16,000');
	await expect(card).toContainText('-2.5%');
	const width = await page.evaluate(() => document.documentElement.scrollWidth);
	expect(width).toBeLessThanOrEqual(390);

	await card.tap();

	const drawer = page.getByRole('dialog');
	await expect(drawer.getByTestId('drawer-title')).toHaveText(
		'1042 Chiller replacement, cold-storage warehouse'
	);
	await page.keyboard.press('Escape');
	await expect(drawer).toBeHidden();
});
