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

		let contentModule = modules[`/src/lib/docs/${filePath}.md`];
		resolvedFilePath = `/src/lib/docs/${filePath}.md`;
		// If not found, try with index.md appended (for directory-style paths)
		if (!contentModule && !filePath.endsWith('.md')) {
			contentModule = modules[`/src/lib/docs/${filePath}/index.md`];
			resolvedFilePath = `/src/lib/docs/${filePath}/index.md`;
		}

		// If still not found, fallback to index
		if (!contentModule) {
			contentModule = modules['/src/lib/docs/index.md'];
		}

		return {
			contentModule: contentModule,
			resolvedFilePath: resolvedFilePath
		};
	}
