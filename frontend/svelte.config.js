import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { execSync } from 'child_process';

const headRev = process.env.GIT_REV || execSync('git rev-parse HEAD').toString().trim();
let dirty = false;
try {
	dirty =
		(process.env.GIT_REV || '').search('dirty') != -1 ||
		(!((process.env.GIT_REV || '').search('dirty') != -1) &&
			execSync('git status --porcelain').toString().trim());
} catch (e) {
	/* empty */
}

const version = dirty ? `${headRev}-dirty-${Date.now().toString()}` : headRev;

console.log(`SvelteKit reloading version: ${version}`);

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: [vitePreprocess({})],

	kit: {
		adapter: adapter(),
		version: {
			name: version
		}
	}
};

export default config;
