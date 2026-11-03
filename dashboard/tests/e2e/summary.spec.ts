import { expect, test } from '@playwright/test';
import { openDashboard } from './helpers';

test('AC-86 badge shows verified, then the rejected answer and its Why?, then verified', async ({
	page
}) => {
	await openDashboard(page);
	const badge = page.getByTestId('summary-badge');
	await expect(badge).toHaveText('Demo AI · numbers verified');
	await expect(page.getByTestId('summary-why')).toHaveCount(0);

	await page.getByTestId('run-picker').selectOption('2026-11-03');

	await expect(badge).toHaveText('Template summary · AI answer rejected');
	const why = page.getByTestId('summary-why');
	await expect(page.getByTestId('summary-why-tokens')).toBeHidden();
	await why.getByText('Why?').click();
	await expect(page.getByTestId('summary-why-tokens')).toBeVisible();
	await expect(page.getByTestId('summary-why-tokens')).toContainText('$13,750');

	await page.getByTestId('run-picker').selectOption('2026-11-04');

	await expect(badge).toHaveText('Demo AI · numbers verified');
	await expect(page.getByTestId('summary-why')).toHaveCount(0);
});

test('AC-87 a job link in the summary opens that job in the drawer', async ({ page }) => {
	await openDashboard(page);
	const link = page.getByTestId('summary-link-1038');
	await expect(link).toHaveText('Level 4 fit-out: VRF install');

	await link.click();

	await expect(page.getByRole('dialog').getByTestId('drawer-title')).toHaveText(
		'1038 Level 4 fit-out: VRF install'
	);
	await page.keyboard.press('Escape');
	await expect(link).toBeFocused();
});
