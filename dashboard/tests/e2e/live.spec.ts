import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';
import { serveFixtures } from './helpers';

// These tests drive the real local helper (`margin-watch serve --pace 0`) on port 4176.
const LIVE = 'http://localhost:4176';
const STEPS = ['read', 'maths', 'review', 'summary', 'excel', 'email', 'dashboard'];

test.use({ baseURL: LIVE });

test.beforeEach(async ({ request }) => {
	const reset = await request.post('/api/reset');
	expect(reset.status()).toBe(204);
});

async function startRun(page: Page): Promise<unknown> {
	const request = page.waitForRequest((r) => r.url().endsWith('/api/run'));
	await page.getByTestId('run-button').click();
	return (await request).postDataJSON();
}

test('AC-100 the Run button shows with the helper and not on a static copy', async ({ page }) => {
	await page.goto('/');

	await expect(page.getByTestId('run-button')).toHaveText(/Run this morning's check/);
	await expect(page.getByTestId('dry-run-pill')).toHaveText('Dry run · nothing is sent');

	await serveFixtures(page, 'runs');
	await page.goto('http://localhost:4174/');
	await expect(page.getByTestId('jobs-table')).toBeVisible();
	await expect(page.getByTestId('run-button')).toHaveCount(0);
});

test('AC-103 real end to end: empty, run, every step done, results and the Excel file', async ({
	page,
	request
}) => {
	await page.goto('/');
	await expect(page.getByTestId('empty-state')).toBeVisible();

	await startRun(page);

	const panel = page.getByTestId('live-panel');
	await expect(panel.getByTestId('live-done')).toHaveText('Done. Nothing was sent.');
	for (const step of STEPS) {
		await expect(panel.getByTestId(`live-step-${step}`)).toHaveAttribute('data-state', 'done');
	}
	const href = await panel.getByTestId('live-excel-link').getAttribute('href');
	expect(href).toBe('/files/margin-report-2026-11-04.xlsx');
	const excel = await request.get(href ?? '');
	expect(excel.status()).toBe(200);
	expect(excel.headers()['content-type']).toContain('spreadsheetml');
	expect((await excel.body()).subarray(0, 2).toString()).toBe('PK');

	await panel.getByTestId('live-results').click();

	await expect(panel).toBeHidden();
	await expect(page.getByTestId('kpi-action').getByTestId('kpi-value')).toHaveText('3');
	await expect(page.getByTestId('kpi-risk').getByTestId('kpi-value')).toHaveText('$66,300');
});

test('AC-101 watching the run: steps, tally, review jobs, verified numbers, links', async ({
	page
}) => {
	await page.goto('/');

	const body = await startRun(page);

	expect(body).toEqual({ ai: 'demo' });
	const panel = page.getByRole('dialog');
	await expect(panel.getByTestId('live-title')).toHaveText('Morning check · dry run');
	await expect(panel.locator('[data-testid^="live-step-"]')).toHaveCount(7);
	await expect(panel.getByTestId('live-done')).toBeVisible();
	await expect(panel.getByTestId('live-step-read')).toContainText(
		'Read 14 jobs from jobs-2026-11-04.json (sample data shaped like a Simpro export).'
	);
	const tally = panel.getByTestId('live-tally');
	for (const text of [/Loss\s*1/, /At risk\s*2/, /Watch\s*2/, /On track\s*7/]) {
		await expect(tally).toContainText(text);
	}
	await expect(panel.getByTestId('live-review')).toContainText('1039');
	await expect(panel.getByTestId('live-review')).toContainText('1044');
	const checks = panel.getByTestId('live-check');
	expect(await checks.count()).toBeGreaterThan(5);
	expect(await checks.evaluateAll((els) => els.every((e) => e.getAttribute('data-ok') === 'true'))).toBe(true);
	await expect(panel.getByTestId('live-step-summary')).toContainText('so it was approved');
	await expect(panel.getByTestId('live-excel-link')).toHaveText(/Open Excel report/);
	await expect(panel.getByTestId('live-email-link')).toHaveAttribute(
		'href',
		'/files/email/preview-2026-11-04.html'
	);
	await expect(panel.getByTestId('live-email-link')).toHaveText(/Preview email/);

	await panel.getByTestId('live-results').click();

	await expect(page.getByRole('dialog')).toHaveCount(0);
	await expect(page.getByTestId('summary-badge')).toHaveText('Demo AI · numbers verified');
});

test('AC-102 the made-up number is caught live and the template is used', async ({ page }) => {
	await page.goto('/');
	await startRun(page);
	const panel = page.getByTestId('live-panel');
	await expect(panel.getByTestId('live-done')).toBeVisible();

	const request = page.waitForRequest((r) => r.url().endsWith('/api/run'));
	await panel.getByTestId('live-try-bad').click();
	expect((await request).postDataJSON()).toEqual({ ai: 'demo-bad' });

	await expect(panel.getByTestId('live-step-summary')).toHaveAttribute('data-state', 'warning');
	const bad = panel.locator('[data-testid="live-check"][data-ok="false"]');
	await expect(bad).toHaveCount(1);
	await expect(bad).toContainText('$13,750');
	await expect(panel.getByTestId('live-step-summary')).toContainText(
		'The answer was rejected and the safe template summary was used instead.'
	);
	await expect(panel.getByTestId('live-done')).toBeVisible();
	await panel.getByTestId('live-results').click();
	await expect(page.getByTestId('summary-badge')).toHaveText(
		'Template summary · AI answer rejected'
	);
});

for (const colorScheme of ['light', 'dark'] as const) {
	test(`AC-104 the live panel is accessible and Esc returns focus (${colorScheme})`, async ({
		page
	}) => {
		await page.emulateMedia({ colorScheme, reducedMotion: 'reduce' });
		await page.goto('/');
		await startRun(page);
		const panel = page.getByRole('dialog');
		await expect(panel.getByTestId('live-done')).toBeVisible();
		expect(await panel.evaluate((el) => el.contains(document.activeElement))).toBe(true);

		const results = await new AxeBuilder({ page }).analyze();
		const serious = results.violations
			.filter((v) => v.impact === 'serious' || v.impact === 'critical')
			.map((v) => `${v.id}: ${v.nodes.map((n) => n.target.join(' ')).join(', ')}`);
		expect(serious).toEqual([]);

		await page.keyboard.press('Escape');

		await expect(panel).toBeHidden();
		await expect(page.getByTestId('run-button')).toBeFocused();
	});
}
