import { expect, test } from '@playwright/test';
import { openDashboard, rowIds, serveFixtures } from './helpers';

test('AC-88 empty index shows the empty state and no table', async ({ page }) => {
	const errors: string[] = [];
	page.on('pageerror', (error) => errors.push(error.message));

	await openDashboard(page, 'runs-empty');

	await expect(page.getByTestId('empty-state')).toHaveText(/No runs yet\. Run margin-watch run\./);
	await expect(page.getByTestId('jobs-table')).toHaveCount(0);
	await page.reload();
	await expect(page.getByTestId('empty-state')).toBeVisible();
	expect(errors).toEqual([]);
});

test('AC-88 loading skeletons show while the index is pending, then the content', async ({
	page
}) => {
	let release = () => {};
	const gate = new Promise<void>((resolve) => {
		release = resolve;
	});
	await serveFixtures(page, 'runs', gate);

	await page.goto('/');

	await expect(page.getByTestId('loading')).toBeVisible();
	await expect(page.getByTestId('jobs-table')).toHaveCount(0);
	release();
	await expect(page.getByTestId('jobs-table')).toBeVisible();
	await expect(page.getByTestId('loading')).toHaveCount(0);
});

test('AC-88 a malformed run file shows an error card and the picker still works', async ({
	page
}) => {
	const errors: string[] = [];
	page.on('pageerror', (error) => errors.push(error.message));

	await openDashboard(page, 'runs-malformed');

	await expect(page.getByTestId('run-error')).toContainText('2026-11-04.json');
	await expect(page.getByTestId('jobs-table')).toHaveCount(0);

	await page.getByTestId('run-picker').selectOption('2026-11-03');

	await expect(page.getByTestId('run-error')).toHaveCount(0);
	await expect(page.getByTestId('jobs-table').locator('tbody tr[data-job-id]')).toHaveCount(14);
	expect((await rowIds(page.getByTestId('jobs-table')))[0]).toBe('1042');
	expect(errors).toEqual([]);
});
