<script lang="ts">
	import A from './defaultMarkdown/a.svelte';
	type BreadcrumbItem = {
		label: string;
		href: string;
	};

	let { path, breadcrumbs }: { path: string, breadcrumbs: string[] } = $props();

	const breadcrumbItems = $derived.by(() => {
		if (!path || path === '/') {
			return [{ label: breadcrumbs[0] || 'Home', href: '/' }];
		}

		const segments = path.split('/').filter(Boolean);
		const items: BreadcrumbItem[] = [{ label: breadcrumbs[0] || 'Home', href: '/' }];

		let currentPath = '';
		for (let i = 0; i < segments.length; i++) {
			const segment = segments[i];
			currentPath += `/${segment}`;
			// Use breadcrumbs prop for label if available, otherwise fall back to segment formatting
			const label = breadcrumbs[i + 1] || segment
				.replace(/[-_]/g, ' ')
				.replace(/\b\w/g, (char) => char.toUpperCase());
			items.push({ label, href: currentPath });
		}

		return items;
	});
</script>

<nav aria-label="Breadcrumb" class="mb-4">
	<ol class="flex items-center space-x-2 text-sm text-gray-500">
		{#each breadcrumbItems as item, index}
			<li class="flex items-center">
				{#if index > 0}
					<i class="fas fa-chevron-right mx-2 h-4 w-4 flex-shrink-0 text-gray-400" aria-hidden="true"></i>
				{/if}
				{#if index === breadcrumbItems.length - 1}
					<span class="font-medium text-gray-900" aria-current="page">
						{item.label}
					</span>
				{:else}
					<A
						href={item.href}
						class="font-medium text-gray-500 hover:text-gray-700 transition-colors duration-150"
					>
						{item.label}
					</A>
				{/if}
			</li>
		{/each}
	</ol>
</nav>
