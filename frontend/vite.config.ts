import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';
import pkg from './package.json' with { type: 'json' };
import { execSync } from 'child_process';

const headRev = process.env.GIT_REV || execSync('git rev-parse HEAD').toString().trim();
let dirty = false;
try {
	dirty =
		(process.env.GIT_REV || '').search('dirty') != -1 ||
		(!((process.env.GIT_REV || '').search('dirty') != -1) &&
			execSync('git status --porcelain').toString().trim()) != '';
} catch (e) {
	/* empty */
}

const versionInfo = {
	version: pkg.version,
	headRev,
	dirty
};

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	},
	server: {
		hmr: {
			port: 33100
		}
	},
	define: {
		__THYMIS_PACKAGE_VERSION__: JSON.stringify(versionInfo)
	}
});
