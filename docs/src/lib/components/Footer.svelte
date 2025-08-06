<script lang="ts">
    import { metadata } from '../docs/SUMMARY.md';
    import A from './defaultMarkdown/a.svelte';
    import { getContext } from 'svelte';

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

    const prefix = getContext<string>('prefix') || '';

    const currentYear = new Date().getFullYear();

    let { resolvedFilePath, currentPath = '' }: { resolvedFilePath?: string; currentPath?: string } = $props();

    // Navigation logic
    const currentPageIndex = $derived.by(() => {
        const cleanCurrentPath = currentPath === '/' ? '/' : currentPath.replace(/\/$/, '');
        return typedMetadata.links.findIndex((link: Link) => {
            const linkPath = link.href === '/' ? '/' : link.href.replace(/\/$/, '');
            let prefixedLinkPath = prefix + linkPath;
            // Handle the case where linkPath is '/' and we have a prefix
            if (linkPath === '/' && prefix) {
                prefixedLinkPath = prefix === '/' ? '/' : prefix.replace(/\/$/, '');
            }
            return prefixedLinkPath === cleanCurrentPath;
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
        return `https://github.com/Thymis-io/thymis/edit/docs-new/docs/src/lib/docs/${cleanPath}`;
    });
</script>

<footer class="border-t border-gray-200 mt-16 pt-8 pb-8">
    <!-- Page Navigation -->
    {#if previousPage || nextPage}
        <div class="max-w-4xl mb-8">
            <div class="flex justify-between items-center">
                <div class="flex-1">
                    {#if previousPage}
                        <A
                            href={previousPage.href}
                            class="group flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            <i class="fas fa-chevron-left w-4 h-4 transform group-hover:-translate-x-1 transition-transform"></i>
                            <div class="text-left">
                                <div class="text-xs text-gray-400 uppercase tracking-wide">Previous</div>
                                <div class="font-medium">{previousPage.text}</div>
                            </div>
                        </A>
                    {/if}
                </div>

                <div class="flex-1 text-right">
                    {#if nextPage}
                        <A
                            href={nextPage.href}
                            class="group flex items-center justify-end space-x-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
                        >
                            <div class="text-right">
                                <div class="text-xs text-gray-400 uppercase tracking-wide">Next</div>
                                <div class="font-medium">{nextPage.text}</div>
                            </div>
                            <i class="fas fa-chevron-right w-4 h-4 transform group-hover:translate-x-1 transition-transform"></i>
                        </A>
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    <div class="max-w-4xl">
        <div class="flex flex-col md:flex-row justify-between items-center text-sm text-gray-600">
            <div class="flex items-center space-x-4 mb-4 md:mb-0">
            </div>

            <div class="flex items-center space-x-4">
                {#if githubEditUrl}
                    <a
                        href={githubEditUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        class="text-xs hover:text-gray-900 transition-colors flex items-center space-x-1"
                    >
                        <i class="fab fa-github w-4 h-4"></i>
                        <span>Edit on GitHub</span>
                    </a>
                {/if}
            </div>
        </div>
    </div>
</footer>
