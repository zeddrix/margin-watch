import { expect, test } from '@playwright/test';
import { RISK_ORDER_4_NOV, openDashboard, rowIds } from './helpers';

test('AC-81 risk order by default, sort by $ at risk, then back to risk order', async ({
	page
}) => {
	await openDashboard(page);
	const table = page.getByTestId('jobs-table');
	await expect(table.locator('tbody tr[data-job-id]')).toHaveCount(14);

	expect(await rowIds(table)).toEqual(RISK_ORDER_4_NOV);
	await expect(page.getByTestId('col-risk')).toHaveAttribute('aria-sort', 'ascending');
	await expect(page.getByTestId('col-at_risk')).toHaveAttribute('aria-sort', 'none');

	await page.getByTestId('sort-at_risk').click();

	await expect(page.getByTestId('col-at_risk')).toHaveAttribute('aria-sort', 'descending');
	await expect(page.getByTestId('col-risk')).toHaveAttribute('aria-sort', 'none');
	expect((await rowIds(table)).slice(0, 6)).toEqual(['1038', '1042', '1035', '1033', '1037', '1040']);

	await page.getByTestId('sort-risk').click();

	await expect(page.getByTestId('col-risk')).toHaveAttribute('aria-sort', 'ascending');
	expect(await rowIds(table)).toEqual(RISK_ORDER_4_NOV);
});

test('AC-82 filter chips and search combine, the count updates, 1038 is marked worse', async ({
	page
}) => {
	await openDashboard(page);
	const table = page.getByTestId('jobs-table');
	const count = page.getByTestId('job-count');
	await expect(count).toHaveText('14 of 14 jobs');
	await expect(page.getByTestId('chip-AT_RISK')).toHaveText(/At risk\s*2/);

	await page.getByTestId('chip-AT_RISK').click();

	await expect(page.getByTestId('chip-AT_RISK')).toHaveAttribute('aria-pressed', 'true');
	await expect(count).toHaveText('2 of 14 jobs');
	expect(await rowIds(table)).toEqual(['1038', '1035']);

	await page.getByTestId('job-search').fill('medical');

	await expect(count).toHaveText('1 of 14 jobs');
	expect(await rowIds(table)).toEqual(['1035']);

	await page.getByTestId('job-search').fill('');
	await page.getByTestId('chip-all').click();

	await expect(count).toHaveText('14 of 14 jobs');
	await expect(page.getByTestId('chip-AT_RISK')).toHaveAttribute('aria-pressed', 'false');
	const worse = table.locator('[data-testid^="worse-"]');
	await expect(worse).toHaveCount(1);
	await expect(page.getByTestId('worse-1038')).toHaveText(/worse since last run/);
});
