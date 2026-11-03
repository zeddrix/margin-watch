import { defineConfig, devices } from '@playwright/test';

// One worker, no retries: a flaky test is a bug (docs/testing-rules.md).
// Port 4174 so tests never collide with `make demo` on 4173.
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
	webServer: {
		command: 'npm run build && npx vite preview --port 4174 --strictPort',
		port: 4174,
		reuseExistingServer: false,
		timeout: 180_000
	}
});
