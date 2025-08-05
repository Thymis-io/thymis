<script lang="ts">
    import { metadata} from '$lib/docs/SUMMARY.md';
    import { page } from '$app/stores';

    // Type definitions for the metadata structure
    interface Link {
        href: string;
        text: string;
    }

    interface Metadata {
        links: Link[];
    }

    // Cast metadata to the proper type
    const typedMetadata = metadata as unknown as Metadata;

    console.log('Metadata:', metadata);
//     Metadata: {
//   layout: 'summary',
//   toc: [],
//   links: [
//     { href: '/', text: 'Introduction' },
//     { href: '/getting_started/', text: 'Getting Started' },
//     { href: '/getting_started/nixos', text: 'Thymis NixOS module' },
//     { href: '/usage/', text: 'Usage' },
//     { href: '/usage/provisioning', text: 'Provisioning a new device' },
//     {
//       href: '/usage/system_configuration',
//       text: 'System Configuration'
//     },
//     { href: '/usage/terminal', text: 'Terminal Usage' },
//     { href: '/usage/vnc', text: 'VNC Usage' },
//     { href: '/architecture', text: 'Architecture' },
//     { href: '/extensions', text: 'Extensions (Under Development)' },
//     { href: '/api', text: 'API' }
//   ]
// }

    const currentYear = new Date().getFullYear();

    let { resolvedFilePath }: { resolvedFilePath?: string } = $props();

    // Navigation logic
    const currentPageIndex = $derived.by(() => {
        const currentPath = $page.url.pathname === '/' ? '/' : $page.url.pathname.replace(/\/$/, '');
        return typedMetadata.links.findIndex((link: Link) => {
            const linkPath = link.href === '/' ? '/' : link.href.replace(/\/$/, '');
            return linkPath === currentPath;
        });
    });

    const previousPage = $derived.by(() => {
        if (currentPageIndex > 0) {
            return typedMetadata.links[currentPageIndex - 1];
        }
        return null;
    });

    const nextPage = $derived.by(() => {
        if (currentPageIndex >= 0 && currentPageIndex < typedMetadata.links.length - 1) {
            return typedMetadata.links[currentPageIndex + 1];
        }
        return null;
    });

    const githubEditUrl = $derived.by(() => {
        if (!resolvedFilePath) return null;
        // Remove leading slash and convert to full GitHub edit URL
        const cleanPath = resolvedFilePath.startsWith('/') ? resolvedFilePath.slice(1) : resolvedFilePath;
        return `https://github.com/Thymis-io/thymis/edit/docs-new/docs/${cleanPath}`;
    });
</script>

<footer class="border-t border-gray-200 mt-16 pt-8 pb-8">
    <!-- Page Navigation -->
    {#if previousPage || nextPage}
        <div class="max-w-4xl mb-8">
            <div class="flex justify-between items-center">
                <div class="flex-1">
                    {#if previousPage}
                        <a
                            href={previousPage.href}
                            class="group flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            <svg class="w-4 h-4 transform group-hover:-translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                            <div class="text-left">
                                <div class="text-xs text-gray-400 uppercase tracking-wide">Previous</div>
                                <div class="font-medium">{previousPage.text}</div>
                            </div>
                        </a>
                    {/if}
                </div>

                <div class="flex-1 text-right">
                    {#if nextPage}
                        <a
                            href={nextPage.href}
                            class="group flex items-center justify-end space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            <div class="text-right">
                                <div class="text-xs text-gray-400 uppercase tracking-wide">Next</div>
                                <div class="font-medium">{nextPage.text}</div>
                            </div>
                            <svg class="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                            </svg>
                        </a>
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    <div class="max-w-4xl">
        <div class="flex flex-col md:flex-row justify-between items-center text-sm text-gray-600">
            <div class="flex items-center space-x-4 mb-4 md:mb-0">
                <span>&copy; {currentYear} Thymis Documentation</span>
                <a href="https://thymis.io" class="hover:text-gray-900 transition-colors">
                    Visit thymis.io
                </a>
            </div>

            <div class="flex items-center space-x-4">
                {#if githubEditUrl}
                    <a
                        href={githubEditUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="text-xs hover:text-gray-900 transition-colors flex items-center space-x-1"
                    >
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clip-rule="evenodd"/>
                        </svg>
                        <span>Edit on GitHub</span>
                    </a>
                {/if}
            </div>
        </div>
    </div>
</footer>
