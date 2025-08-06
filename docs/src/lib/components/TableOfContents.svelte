<script lang="ts">
	import GithubSlugger from 'github-slugger';
	import { onMount } from 'svelte';

	let { toc } = $props();

	// Transform the toc data to include generated IDs
	const tocItems = $derived.by(() => {
		const slugger = new GithubSlugger();
		return toc.map((item) => ({
			...item,
			id: item.id || slugger.slug(item.text)
		}));
	});

	// Track active section
	let activeId = $state('');

	onMount(() => {
		const observerOptions = {
			rootMargin: '-20% 0px -35% 0px',
			threshold: 0
		};

		const observer = new IntersectionObserver((entries) => {
			// Find the first visible entry with the highest position on screen
			const visibleEntries = entries.filter(entry => entry.isIntersecting);

			if (visibleEntries.length > 0) {
				// Sort by position on screen (top to bottom)
				visibleEntries.sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
				activeId = visibleEntries[0].target.id;
			}
		}, observerOptions);

		// Observe all elements that have IDs matching our TOC items
		tocItems.forEach(item => {
			const element = document.getElementById(item.id);
			if (element) {
				observer.observe(element);
			}
		});

		return () => {
			observer.disconnect();
		};
	});
</script>

<div class="sticky top-8">
	<h3 class="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-900">On this page</h3>

	{#if tocItems.length > 0}
		<nav>
			<ul class="space-y-2 text-sm">
				{#each tocItems as item}
					<li>
						<a
							href="#{item.id}"
							class="block py-1 transition-colors duration-200"
							class:font-medium={item.level === 1}
							class:pl-0={item.level === 1}
							class:pl-3={item.level === 2}
							class:pl-6={item.level === 3}
							class:text-blue-600={activeId === item.id}
							class:font-semibold={activeId === item.id}
							class:text-gray-600={activeId !== item.id}
							class:hover:text-gray-900={activeId !== item.id}
						>
							{item.text}
						</a>
					</li>
				{/each}
			</ul>
		</nav>
	{:else}
		<div class="text-sm text-gray-500">Table of contents will be populated automatically</div>
	{/if}
</div>
