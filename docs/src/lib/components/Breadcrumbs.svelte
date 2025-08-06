<script lang="ts">
	import A from './defaultMarkdown/a.svelte';
	type BreadcrumbItem = {
		label: string;
		href: string;
	};

	let { path }: { path: string } = $props();

	const breadcrumbs = $derived.by(() => {
		if (!path || path === '/') {
			return [{ label: 'Home', href: '/' }];
		}

		const segments = path.split('/').filter(Boolean);
		const items: BreadcrumbItem[] = [{ label: 'Home', href: '/' }];

		let currentPath = '';
		for (const segment of segments) {
			currentPath += `/${segment}`;
			// Convert segment to a more readable label (capitalize and replace hyphens/underscores)
			const label = segment
				.replace(/[-_]/g, ' ')
				.replace(/\b\w/g, (char) => char.toUpperCase());
			items.push({ label, href: currentPath });
		}

		return items;
	});
</script>

<nav aria-label="Breadcrumb" class="mb-4">
	<ol class="flex items-center space-x-2 text-sm text-gray-500">
		{#each breadcrumbs as item, index}
			<li class="flex items-center">
				{#if index > 0}
					<i class="fas fa-chevron-right mx-2 h-4 w-4 flex-shrink-0 text-gray-400" aria-hidden="true"></i>
				{/if}
				{#if index === breadcrumbs.length - 1}
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
