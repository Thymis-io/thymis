import type { SvelteComponent } from 'svelte';

const modules = import.meta.glob('./**/*.md', { eager: true }) as Record<
    string,
    { default: typeof SvelteComponent; metadata?: Record<string, unknown> }
>;

export default (path: string | string[]) => {
    const splitPath = typeof path === 'string' ? path.split('/') : path;
		const filePath =
			splitPath && Array.isArray(splitPath) && splitPath.length > 0 ? splitPath.join('/') : 'index';
		let resolvedFilePath;

		// Clean up the filePath to avoid double slashes
		const cleanFilePath = filePath.replace(/\/+/g, '/').replace(/^\/|\/$/g, '') || 'index';

		let contentModule = modules[`./${cleanFilePath}.md`];
		resolvedFilePath = `./${cleanFilePath}.md`;
		// If not found, try with index.md appended (for directory-style paths)
		if (!contentModule && !cleanFilePath.endsWith('.md')) {
			contentModule = modules[`./${cleanFilePath}/index.md`];
			resolvedFilePath = `./${cleanFilePath}/index.md`;
		}

		// If still not found, fallback to index
		if (!contentModule) {
			contentModule = modules['./index.md'];
			resolvedFilePath = './index.md';
		}

		return {
			contentModule: contentModule,
			resolvedFilePath: resolvedFilePath
		};
	}
