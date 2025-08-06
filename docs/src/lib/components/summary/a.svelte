<script lang="ts">
    import { getContext } from 'svelte';
	import type { Writable } from 'svelte/store';

    let { href, children } = $props();

    // Get prefix from context
    const prefix = getContext<string>('prefix') || '';

    let shouldGetPrefixed = $derived(href.startsWith('/') || href.startsWith('./'));

    // Get the navigation context if it exists
    // const navigationContext = getContext<{ onNavigate?: () => void; currentPath?: string }>('navigation');
    const onNavigate = getContext<() => void|undefined>('onNavigate');
    const currentPathStore = $derived(getContext<Writable<string>>('currentPath') || '');

    function isCurrentPage(linkHref: string): boolean {
        // Apply prefix to linkHref for comparison
        const prefixedHref = shouldGetPrefixed ? `${prefix}${linkHref}` : linkHref;
        // Remove trailing slash and compare with current pathname
        const cleanHref = prefixedHref === '/' ? '/' : prefixedHref.replace(/\/$/, '');
        const cleanPathname = $currentPathStore === '/' ? '/' : $currentPathStore.replace(/\/$/, '');
        return cleanPathname === cleanHref;
    }

    function isInHierarchy(linkHref: string): boolean {
        // For root links, we don't want hierarchy highlighting - they should only be highlighted via isCurrentPage
        if (linkHref === '/') {
            return false;
        }

        // Apply prefix to linkHref for comparison
        const prefixedHref = shouldGetPrefixed ? `${prefix}${linkHref}` : linkHref;
        // Check if current page is within this link's hierarchy
        const cleanHref = prefixedHref === '/' ? '/' : prefixedHref.replace(/\/$/, '');
        const cleanPathname = $currentPathStore === '/' ? '/' : $currentPathStore.replace(/\/$/, '');

        // For non-root links, check if current path starts with the link href (making it a parent)
        return cleanPathname.startsWith(cleanHref + '/');
    }

    function handleClick() {
        // Call the onNavigate function if it exists
        if (onNavigate) {
            onNavigate();
        }
    }

    let finalHref = $derived(
        shouldGetPrefixed ? `${prefix}${href}` : href
    );
</script>
<a
    href={finalHref}
    onclick={handleClick}
    class="block px-3 py-2 text-sm rounded-md transition-colors no-underline {
        isCurrentPage(href)
            ? 'bg-blue-50 text-blue-700 font-medium'
            : isInHierarchy(href)
                ? 'bg-slate-100 text-blue-600'
                : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
    }"
>
    {@render children()}
</a>
