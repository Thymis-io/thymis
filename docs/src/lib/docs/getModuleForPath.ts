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

		let contentModule = modules[`./${filePath}.md`];
		resolvedFilePath = `./${filePath}.md`;
		// If not found, try with index.md appended (for directory-style paths)
		if (!contentModule && !filePath.endsWith('.md')) {
			contentModule = modules[`./${filePath}/index.md`];
			resolvedFilePath = `./${filePath}/index.md`;
		}

		// If still not found, fallback to index
		if (!contentModule) {
			contentModule = modules['./index.md'];
		}

		return {
			contentModule: contentModule,
			resolvedFilePath: resolvedFilePath
		};
	}
