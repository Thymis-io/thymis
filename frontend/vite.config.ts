import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { execSync } from 'child_process';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import tailwindcss from '@tailwindcss/vite';
import pkg from './package.json' with { type: 'json' };

const headRev = process.env.GIT_REV || execSync('git rev-parse HEAD').toString().trim();
let dirty = false;
try {
	dirty =
		(process.env.GIT_REV || '').search('dirty') != -1 ||
		(!((process.env.GIT_REV || '').search('dirty') != -1) &&
			execSync('git status --porcelain').toString().trim()) != '';
} catch (e) {}

/* empty */ const versionInfo = { version: pkg.version, headRev, dirty };

const target = ['es2024', 'chrome122', 'edge122', 'safari17', 'firefox127', 'opera108'];

const headRev2 = process.env.GIT_REV || execSync('git rev-parse HEAD').toString().trim();
let dirty2 = false;

try {
	dirty2 =
		(process.env.GIT_REV || '').search('dirty') != -1 ||
		(!((process.env.GIT_REV || '').search('dirty') != -1) &&
			execSync('git status --porcelain').toString().trim()) != '';
} catch (e) {}

/* empty */ const version = dirty2 ? `${headRev2}-dirty-${Date.now().toString()}` : headRev2;

console.log(`SvelteKit reloading version: ${version}`);

export default defineConfig({
	plugins: [
		sveltekit({
			// Consult https://kit.svelte.dev/docs/integrations#preprocessors
			// for more information about preprocessors
			preprocess: [vitePreprocess({})],
			adapter: adapter(),
			version: { name: version }
		}),
		tailwindcss()
	],
	test: { include: ['src/**/*.{test,spec}.{js,ts}'] },
	server: {
		hmr: {
			port: parseInt(process.env.VITE_HMR_PORT || '0') || undefined
		}
	},
	define: { __THYMIS_PACKAGE_VERSION__: JSON.stringify(versionInfo) },
	build: { target },
	optimizeDeps: {}
});
