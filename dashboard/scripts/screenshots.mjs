// Visual review screenshots: node scripts/screenshots.mjs [baseURL] [outDir]
// Needs a running build (e.g. `npx vite preview --port 4175`). Serves the committed fixtures.
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '@playwright/test';

const here = dirname(fileURLToPath(import.meta.url));
const baseURL = process.argv[2] ?? 'http://localhost:4175';
const outDir = process.argv[3] ?? join(here, '..', '..', 'docs', 'screenshots');
const fixtures = join(here, '..', 'tests', 'fixtures', 'runs');
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const shots = [];
for (const scheme of ['light', 'dark']) {
	for (const width of [1280, 1024, 390]) {
		const context = await browser.newContext({
			viewport: { width, height: width === 390 ? 844 : 900 },
			deviceScaleFactor: 1,
			colorScheme: scheme,
			timezoneId: 'Australia/Melbourne',
			locale: 'en-AU',
			reducedMotion: 'reduce'
		});
		const page = await context.newPage();
		await page.route('**/runs/*.json', async (route) => {
			const file = join(fixtures, new URL(route.request().url()).pathname.split('/').pop());
			if (existsSync(file)) await route.fulfill({ path: file, contentType: 'application/json' });
			else await route.fulfill({ status: 404, body: '' });
		});
		await page.goto(baseURL);
		await page.getByTestId('jobs-table').waitFor({ state: 'attached' });
		const name = `dashboard-${width}-${scheme}.png`;
		await page.screenshot({ path: join(outDir, name), fullPage: true });
		shots.push(name);
		if (width !== 1024) {
			const target = width === 390 ? 'job-card-1042' : 'job-row-1042';
			await page.getByTestId(target).click();
			await page.getByRole('dialog').waitFor();
			const drawer = `drawer-${width}-${scheme}.png`;
			await page.screenshot({ path: join(outDir, drawer) });
			shots.push(drawer);
		}
		await context.close();
	}
}
await browser.close();
console.log(shots.map((s) => join(outDir, s)).join('\n'));
