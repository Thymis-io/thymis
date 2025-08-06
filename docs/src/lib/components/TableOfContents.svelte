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
		// Function to determine which section is currently active
		const updateActiveSection = () => {
			const sections = tocItems.map(item => {
				const element = document.getElementById(item.id);
				return element ? { id: item.id, element } : null;
			}).filter(Boolean);

			if (sections.length === 0) return;

			// If we're at the very top of the page, always select the first section
			if (window.scrollY <= 1) {
				activeId = sections[0].id;
				return;
			}

			// Find the section that should be highlighted
			let bestMatch = sections[0].id; // Default to first section

			// Calculate 40% line from top of viewport
			const viewportHeight = window.innerHeight;
			const fortyPercentFromTop = viewportHeight * 0.4;

			// Go through sections and find the one that should be active
			for (let i = 0; i < sections.length; i++) {
				const { id, element } = sections[i];
				const rect = element.getBoundingClientRect();

				// A section is "active" if its top has reached the 40% line from top
				if (rect.top <= fortyPercentFromTop) {
					bestMatch = id;
				}
			}

			activeId = bestMatch;
		};

		// Initial update
		updateActiveSection();

		// Listen for scroll events with throttling
		let ticking = false;
		const handleScroll = () => {
			if (!ticking) {
				requestAnimationFrame(() => {
					updateActiveSection();
					ticking = false;
				});
				ticking = true;
			}
		};

		// Listen for hash changes (when clicking TOC links)
		const handleHashChange = () => {
			// Small delay to ensure scroll has completed
			setTimeout(updateActiveSection, 100);
		};

		window.addEventListener('scroll', handleScroll);
		window.addEventListener('hashchange', handleHashChange);

		return () => {
			window.removeEventListener('scroll', handleScroll);
			window.removeEventListener('hashchange', handleHashChange);
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
