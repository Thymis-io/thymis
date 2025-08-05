<script lang="ts">
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';

    interface NavItem {
        label: string;
        href: string;
        children?: NavItem[];
    }

    // Navigation items structure
    const navigationItems: NavItem[] = [
        { label: 'Introduction', href: '/index' },
        {
            label: 'Getting Started',
            href: '/getting_started/index',
            children: [
                { label: 'Thymis NixOS module', href: '/getting_started/nixos' }
            ]
        },
        {
            label: 'Usage',
            href: '/usage/index',
            children: [
                { label: 'Provisioning a new device', href: '/usage/provisioning' },
                { label: 'System Configuration', href: '/usage/system_configuration' },
                { label: 'Terminal Usage', href: '/usage/terminal' },
                { label: 'VNC Usage', href: '/usage/vnc' }
            ]
        },
        { label: 'Architecture', href: '/architecture' },
        { label: 'Extensions (Under Development)', href: '/extensions' },
        { label: 'API', href: '/api' }
    ];

    function handleNavigation(href: string, event: Event) {
        event.preventDefault();
        goto(href);
    }

    function isCurrentPage(href: string): boolean {
        return $page.url.pathname === href;
    }

    function isParentOfCurrentPage(item: NavItem): boolean {
        if (!item.children) return false;
        return item.children.some((child) => isCurrentPage(child.href));
    }
</script>

<nav class="space-y-1">
    <h2 class="text-sm font-semibold text-gray-900 mb-4">Documentation</h2>

    {#each navigationItems as item}
        <div class="space-y-1">
            <a
                href={item.href}
                onclick={(e) => handleNavigation(item.href, e)}
                class="block px-3 py-2 text-sm rounded-md transition-colors {
                    isCurrentPage(item.href) || isParentOfCurrentPage(item)
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                }"
            >
                {item.label}
            </a>

            {#if item.children}
                <div class="ml-4 space-y-1">
                    {#each item.children as child}
                        <a
                            href={child.href}
                            onclick={(e) => handleNavigation(child.href, e)}
                            class="block px-3 py-2 text-sm rounded-md transition-colors {
                                isCurrentPage(child.href)
                                    ? 'bg-blue-50 text-blue-700 font-medium'
                                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                            }"
                        >
                            {child.label}
                        </a>
                    {/each}
                </div>
            {/if}
        </div>
    {/each}
</nav>
