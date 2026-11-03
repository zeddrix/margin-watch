import { expect, test } from '@playwright/test';
import { openDashboard } from './helpers';

test('AC-80 top bar and KPI tiles match the latest run, then the 3 Nov run', async ({ page }) => {
	await openDashboard(page);

	await expect(page.getByTestId('wordmark')).toHaveText('Margin Watch');
	await expect(page.getByTestId('run-stamp')).toHaveText('Run Wed 4 Nov 2026, 6:30 AM Melbourne');
	await expect(page.getByTestId('sample-pill')).toHaveText('Sample data');
	const picker = page.getByTestId('run-picker');
	await expect(picker.locator('option')).toHaveText(['Wed 4 Nov 2026', 'Tue 3 Nov 2026']);

	const tile = (id: string) => ({
		value: page.getByTestId(id).getByTestId('kpi-value'),
		context: page.getByTestId(id).getByTestId('kpi-context')
	});
	await expect(tile('kpi-action').value).toHaveText('3');
	await expect(tile('kpi-action').context).toHaveText('+1 since Tue 3 Nov');
	await expect(tile('kpi-risk').value).toHaveText('$66,300');
	await expect(tile('kpi-risk').context).toHaveText('+$7,500 since Tue 3 Nov');
	await expect(tile('kpi-margin').value).toHaveText('15.7%');
	await expect(tile('kpi-margin').context).toHaveText('-0.6 pts since Tue 3 Nov');
	await expect(tile('kpi-review').value).toHaveText('2');
	await expect(tile('kpi-review').context).toHaveText('No change since Tue 3 Nov');

	await picker.selectOption('2026-11-03');

	await expect(page.getByTestId('run-stamp')).toHaveText('Run Tue 3 Nov 2026, 6:30 AM Melbourne');
	await expect(tile('kpi-action').value).toHaveText('2');
	await expect(tile('kpi-risk').value).toHaveText('$58,800');
	await expect(tile('kpi-margin').value).toHaveText('16.3%');
	await expect(tile('kpi-review').value).toHaveText('2');
	for (const id of ['kpi-action', 'kpi-risk', 'kpi-margin', 'kpi-review']) {
		await expect(tile(id).context).toHaveText('First run');
	}
});
