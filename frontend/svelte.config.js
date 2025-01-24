import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import { execSync } from 'child_process';

// get current head rev
const headRev = execSync('git rev-parse HEAD').toString().trim();
// if dirty, append "dirty-Date.now().toString()"
const dirty = execSync('git status --porcelain').toString().trim();
const version = dirty ? `${headRev}-dirty-${Date.now().toString()}` : headRev;

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: [vitePreprocess({})],

	kit: {
		adapter: adapter(),
		version: version
	}
};

export default config;
