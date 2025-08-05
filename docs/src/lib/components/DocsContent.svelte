<script lang="ts">
	let {
		path
	}: {
		path: string | string[];
	} = $props();
	const modules = import.meta.glob('$lib/docs/**/*.md', { eager: true }) as Record<
		string,
		{ default: unknown; metadata?: unknown }
	>;

	let ContentModule = $derived.by(() => {
		const splitPath = typeof path === 'string' ? path.split('/') : path;
		const filePath =
			splitPath && Array.isArray(splitPath) && splitPath.length > 0 ? splitPath.join('/') : 'index';

		let contentModule = modules[`/src/lib/docs/${filePath}.md`];
		// If not found, try with index.md appended (for directory-style paths)
		if (!contentModule && !filePath.endsWith('.md')) {
			contentModule = modules[`/src/lib/docs/${filePath}/index.md`];
		}

		// If still not found, fallback to index
		if (!contentModule) {
			console.warn(`Content module not found for path: ${filePath}. Falling back to index.md.`);
			contentModule = modules['/src/lib/docs/index.md'];
		}

		console.log('Content module loaded:', contentModule, 'for path:', filePath);
		console.log('Metadata:', contentModule?.metadata);

		return contentModule ? (contentModule.default as any) : null;
	});

	$effect(() => {
		console.log('ContentModule updated:', ContentModule);
		console.log('Path:', path);
	});
</script>

<ContentModule />
