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

		// If still not found, fallback to index
		if (!contentModule) {
			contentModule = modules['./index.md'];
			resolvedFilePath = './index.md';
		}

		// we will also build breadcrumbs. To go up a path, remove last segment so from a/b/c we get a/b and look at a/b.md
		// when doing a.md, we look at index.md afterwards
		// for each of them, we will use .metadata.toc
		const breadcrumbs = [];
		const ancestorAndSelf = [];
		// Insert index always
		ancestorAndSelf.push(modules['./index.md']);
		// if we are not index (nothing), add more
		if (cleanFilePath !== 'index') {
			const segments = cleanFilePath.split('/');
			for (let i = 0; i <= segments.length; i++) {
				const parentPath = segments.slice(0, i).join('/');
				const parentModule = modules[`./${parentPath}.md`];
				if (parentModule) {
					ancestorAndSelf.push(parentModule);
				}
			}
		}


		// collect breadcrumbs from parent modules like this:
		// module.metadata.toc
		for (const parentModule of ancestorAndSelf) {
			if (parentModule.metadata && parentModule.metadata.toc) {
				//Breadcrumbs for module: [ { level: 1, text: 'Introduction', id: null } ]
				// select the first item in the toc
				const firstItem = parentModule.metadata.toc[0] || null;
				if (firstItem) {
					breadcrumbs.push(firstItem.text);
				}
			}
		}

		return {
			contentModule: contentModule,
			resolvedFilePath: resolvedFilePath,
			breadcrumbs: breadcrumbs,
		};
	}

// index of all
export const allModules = Object.entries(modules).map(([path, module]) => {
	return {
		path,
		module
	};
});

export const should404 = (path: string) => {
	if (path === '') {
		return !modules['./index.md'];
	}
	const module = modules[`./${path}.md`];
	return !module;
};
