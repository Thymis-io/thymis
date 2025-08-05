export const load = async ({ params }: { params: Record<string, string | string[]> }) => {
	const path = params.path;

	// If no path is provided, default to index
	const filePath = path && Array.isArray(path) && path.length > 0 ? path.join('/') : 'index';

	// Import all markdown modules
	const modules = import.meta.glob('$lib/docs/**/*.md', { eager: true }) as Record<string, { default: unknown }>;

	return {
		currentPath: filePath,
		path: params.path,
		allModules: Object.keys(modules).map(key => key.replace('/src/lib/docs/', '').replace('.md', ''))
	};
};
