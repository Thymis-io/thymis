<script lang="ts">
    import { page } from '$app/stores';

    let { href, children } = $props();

    function isCurrentPage(linkHref: string): boolean {
        // Remove trailing slash and compare with current pathname
        const cleanHref = linkHref === '/' ? '/' : linkHref.replace(/\/$/, '');
        const cleanPathname = $page.url.pathname === '/' ? '/' : $page.url.pathname.replace(/\/$/, '');
        return cleanPathname === cleanHref;
    }
</script>
<a
    {href}
    class="block px-3 py-2 text-sm rounded-md transition-colors no-underline {
        isCurrentPage(href)
            ? 'bg-blue-50 text-blue-700 font-medium'
            : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
    }"
>
    {@render children()}
</a>
