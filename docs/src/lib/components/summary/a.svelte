<script lang="ts">
	import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import { afterNavigate } from '$app/navigation';
	import scrollIntoView from 'scroll-into-view-if-needed';

	let { href, children } = $props();

	// Get prefix from context
	const prefix = getContext<string>('prefix') || '';

	let shouldGetPrefixed = true;

	// Get the navigation context if it exists
	// const navigationContext = getContext<{ onNavigate?: () => void; prefixedPath?: string }>('navigation');
	const onNavigate = getContext<() => void | undefined>('onNavigate');
	const prefixedPathStore = $derived(getContext<Writable<string>>('prefixedPath') || '');

	function isCurrentPage(linkHref: string): boolean {
		// Apply prefix to linkHref for comparison
		const prefixedHref = shouldGetPrefixed ? `${prefix}/${linkHref}` : `/${linkHref}`;
		// Remove trailing slash and compare with current pathname
		const cleanHref = prefixedHref === '/' ? '/' : prefixedHref.replace(/\/$/, '');
		// remove .md and index.md
		const cleanHrefWithoutMd = cleanHref.endsWith('.md') ? cleanHref.slice(0, -3) : cleanHref;
		const cleanHrefWithoutIndex = cleanHrefWithoutMd.endsWith('index')
			? cleanHrefWithoutMd.slice(0, -5)
			: cleanHrefWithoutMd;
		// remove trailing slash for href
		const theHref = cleanHrefWithoutIndex === '/' ? '/' : cleanHrefWithoutIndex.replace(/\/$/, '');
		const cleanPathname = $prefixedPathStore === '/' ? '/' : $prefixedPathStore.replace(/\/$/, '');
		return cleanPathname === theHref;
	}

	function isInHierarchy(linkHref: string): boolean {
		// For root links, we don't want hierarchy highlighting - they should only be highlighted via isCurrentPage
		if (linkHref === 'index.md') {
			return false;
		}

		// Apply prefix to linkHref for comparison
		const prefixedHref = shouldGetPrefixed ? `${prefix}/${linkHref}` : `/${linkHref}`;
		// Check if current page is within this link's hierarchy
		const cleanHref = prefixedHref === '/' ? '/' : prefixedHref.replace(/\/$/, '');
		// remove .md and index.md
		const cleanHrefWithoutMd = cleanHref.endsWith('.md') ? cleanHref.slice(0, -3) : cleanHref;
		const cleanHrefWithoutIndex = cleanHrefWithoutMd.endsWith('index')
			? cleanHrefWithoutMd.slice(0, -5)
			: cleanHrefWithoutMd;
		// remove trailing slash for href
		const theHref = cleanHrefWithoutIndex === '/' ? '/' : cleanHrefWithoutIndex.replace(/\/$/, '');
		const cleanPathname = $prefixedPathStore === '/' ? '/' : $prefixedPathStore.replace(/\/$/, '');

		// For non-root links, check if current path starts with the link href (making it a parent)
		return cleanPathname.startsWith(theHref + '/');
	}

	function handleClick() {
		// Call the onNavigate function if it exists
		if (onNavigate) {
			onNavigate();
		}
	}

	let finalHref = $derived.by(() => {
		let cleanedHref = href.endsWith('.md') ? href.slice(0, -3) : href; // Remove '.md' if it exists
		// if path ends with "index", remove it
		if (cleanedHref.endsWith('index')) {
			cleanedHref = cleanedHref.slice(0, -5); // Remove '/index' (5 characters)
		}
		// add slash
		cleanedHref = cleanedHref.startsWith('/') ? cleanedHref : `/${cleanedHref}`;
		return shouldGetPrefixed ? `${prefix}${cleanedHref}` : cleanedHref;
	});

	let element: HTMLAnchorElement | null = $state(null);

	afterNavigate(() => {
		// if is current page, scroll into view
		if (isCurrentPage(href)) {
			// element?.scrollIntoView({
			//     behavior: 'smooth',
			//     block: 'nearest',
			//     container: 'nearest'
			// });
			if (element) {
				scrollIntoView(element, {
					behavior: 'smooth',
					block: 'center',
					boundary: document.querySelector('.summary-nav') || document.body,
					scrollMode: 'if-needed'
				});
			}
		}
	});
</script>

<a
	href={finalHref}
	onclick={handleClick}
	bind:this={element}
	class="block rounded-md px-3 py-2 text-sm no-underline transition-colors {isCurrentPage(href)
		? 'bg-blue-50 font-medium text-blue-700'
		: isInHierarchy(href)
			? 'bg-slate-100 text-blue-600'
			: 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'}"
>
	{@render children()}
</a>
