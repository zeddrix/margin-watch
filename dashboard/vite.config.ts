import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// A static site: the dashboard only reads the run files in static/runs/.
			adapter: adapter()
		})
	],
	test: {
		expect: { requireAssertions: true },
		include: ['tests/unit/**/*.test.ts'],
		environment: 'node'
	}
});
