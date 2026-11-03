import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { openDashboard } from './helpers';

async function seriousViolations(page: Page): Promise<string[]> {
	const results = await new AxeBuilder({ page }).analyze();
	return results.violations
		.filter((v) => v.impact === 'serious' || v.impact === 'critical')
		.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`);
}

for (const colorScheme of ['light', 'dark'] as const) {
	test(`AC-90 no serious or critical axe violations on the page and open drawer (${colorScheme})`, async ({
		page
	}) => {
		await page.emulateMedia({ colorScheme, reducedMotion: 'reduce' });
		await openDashboard(page);
		await expect(page.getByTestId('jobs-table')).toBeVisible();

		expect(await seriousViolations(page)).toEqual([]);

		await page.getByTestId('job-row-1042').click();
		await expect(page.getByRole('dialog')).toBeVisible();

		expect(await seriousViolations(page)).toEqual([]);

		await page.getByTestId('run-picker').selectOption('2026-11-03');
		await expect(page.getByTestId('summary-badge')).toHaveText(/AI answer rejected/);
		expect(await seriousViolations(page)).toEqual([]);
	});
}
