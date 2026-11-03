import { defineConfig, devices } from '@playwright/test';

// One worker, no retries: a flaky test is a bug (docs/testing-rules.md).
// Port 4174: the static build (fixtures served by the tests). Port 4176: the real local helper
// (`margin-watch serve`, no pacing, its own output folder) for the live-run tests.
// Neither collides with `make demo` on 4173.
export default defineConfig({
	testDir: 'tests/e2e',
	testMatch: '**/*.spec.ts',
	workers: 1,
	retries: 0,
	fullyParallel: false,
	forbidOnly: true,
	reporter: [['list'], ['html', { open: 'never' }]],
	use: {
		baseURL: 'http://localhost:4174',
		trace: 'retain-on-failure',
		timezoneId: 'Australia/Melbourne',
		locale: 'en-AU'
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	webServer: [
		{
			command: 'npm run build && npx vite preview --port 4174 --strictPort',
			port: 4174,
			reuseExistingServer: false,
			timeout: 180_000
		},
		{
			command:
				'cd ../agent && MARGIN_WATCH_ENV_FILE= uv run margin-watch serve --port 4176 --pace 0 --output-dir ../.e2e-live --dashboard-dir ../dashboard/build',
			port: 4176,
			reuseExistingServer: false,
			timeout: 180_000
		}
	]
});
