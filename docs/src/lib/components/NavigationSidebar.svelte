<script lang="ts">
  import WordCountDistributionDocs from './WordCountDistributionDocs.svelte';

    import { setContext, onMount, getContext } from 'svelte';
    import Summary from '../docs/SUMMARY.md';
    import { writable } from 'svelte/store';
    import { Index } from 'flexsearch';
    import { afterNavigate } from '$app/navigation';
	import { dev } from '$app/environment';


    interface Props {
        onNavigate?: () => void;
        allModules?: Record<string, any> | Array<{path: string, module: any}>; // Support both formats
    }

    let { onNavigate, allModules = {} }: Props = $props();

    // Get prefix from context if available
    const prefix = getContext<string>('prefix') || '';

    // Create FlexSearch index
    let searchIndex: Index;
    let searchResults = writable<Array<{ id: string; title: string; path: string; excerpt: string }>>([]);
    let searchQuery = $state('');
    let showSearchModal = $state(false);
    let searchInputRef: HTMLInputElement|null = $state(null);
    let searchModalRef: HTMLDivElement|null = $state(null);

    // Cache for processed modules to avoid repeated lookups and processing
    let moduleCache = $state(new Map<string, { moduleData: any; cleanContent: string; title: string }>());

    // Initialize FlexSearch and index modules
    onMount(() => {
        searchIndex = new Index({
            preset: 'performance',
            tokenize: 'bidirectional',
            encoder: 'LatinExtra',
            resolution: 9,
        });

        // Index all modules' markdown content and build cache
        if (Array.isArray(allModules)) {
            allModules.forEach(({ path, module }) => {
                const cleanPath = path.replace(/^\.\//, '').replace(/\.md$/, '');
                const fullContent = module?.metadata?.contents || module?.metadata?.fm?.contents || '';

                // Exclude SUMMARY.md from search indexing
                if (fullContent && !cleanPath.includes('SUMMARY') && !path.includes('SUMMARY.md')) {
                    searchIndex.add(cleanPath, fullContent);

                    // Pre-process and cache module data
                    const cleanContent = preprocessContent(fullContent);
                    const title = module?.metadata?.toc?.[0]?.text ||
                                cleanPath.split('/').pop()?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) ||
                                cleanPath;

                    moduleCache.set(cleanPath, {
                        moduleData: module,
                        cleanContent,
                        title
                    });
                }
            });
        } else {
            Object.entries(allModules).forEach(([path, module]) => {
                const fullContent = module?.metadata?.contents || module?.metadata?.fm?.contents || '';

                // Exclude SUMMARY.md from search indexing
                if (fullContent && !path.includes('SUMMARY') && !path.includes('SUMMARY.md')) {
                    searchIndex.add(path, fullContent);

                    // Pre-process and cache module data
                    const cleanContent = preprocessContent(fullContent);
                    const title = module?.metadata?.toc?.[0]?.text ||
                                path.split('/').pop()?.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()) ||
                                path;

                    moduleCache.set(path, {
                        moduleData: module,
                        cleanContent,
                        title
                    });
                }
            });
        }
    });

    // Pre-process content to remove markdown syntax (done once during initialization)
    function preprocessContent(content: string): string {
        return content
            .replace(/#{1,6}\s+/g, '') // Remove markdown headers
            .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold markdown
            .replace(/\*([^*]+)\*/g, '$1') // Remove italic markdown
            .replace(/`([^`]+)`/g, '$1') // Remove inline code markdown
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Convert links to just text
            .replace(/\n\s*\n/g, ' ') // Replace multiple newlines with space
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim();
    }

    // Search function
    function performSearch(query: string) {
        if (!searchIndex || !query.trim()) {
            searchResults.set([]);
            return;
        }

        const results = searchIndex.search(query, { limit: 8, suggest:true });
        const searchResultsData = results.map((id) => {
            const idString = String(id);
            const cached = moduleCache.get(idString);

            if (!cached) {
                return null; // Skip if not found in cache
            }

            const excerpt = generateExcerpt(cached.cleanContent, query);

            // Construct proper path with prefix
            let resultPath;
            if (idString === 'index') {
                resultPath = prefix ? `${prefix}/` : '/';
            } else {
                resultPath = prefix ? `${prefix}/${idString}` : `/${idString}`;
            }

            return {
                id: idString,
                title: cached.title,
                path: resultPath,
                excerpt: excerpt
            };
        }).filter((result): result is { id: string; title: string; path: string; excerpt: string } => result !== null);

        searchResults.set(searchResultsData);
    }

    // Open search modal
    function openSearchModal() {
        showSearchModal = true;
        // Focus the search input after modal opens
        setTimeout(() => {
            searchInputRef?.focus();
        }, 100);
    }

    // Close search modal
    function closeSearchModal() {
        showSearchModal = false;
        searchQuery = '';
        searchResults.set([]);
    }

    // Generate excerpt with context around search term (optimized)
    function generateExcerpt(cleanContent: string, searchTerm: string): string {
        if (!cleanContent || !searchTerm) return '';

        const lowerContent = cleanContent.toLowerCase();
        const lowerSearchTerm = searchTerm.toLowerCase();
        const index = lowerContent.indexOf(lowerSearchTerm);

        if (index === -1) {
            // If search term not found, return first part of content
            const excerpt = cleanContent.substring(0, 200);
            return excerpt.length < cleanContent.length ? excerpt + '...' : excerpt;
        }

        const start = Math.max(0, index - 100);
        const end = Math.min(cleanContent.length, index + searchTerm.length + 100);

        let excerpt = cleanContent.substring(start, end);
        if (start > 0) excerpt = '...' + excerpt;
        if (end < cleanContent.length) excerpt = excerpt + '...';

        // Highlight the search term (case insensitive) - only operation left here
        const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        excerpt = excerpt.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');

        return excerpt;
    }

    // Keyboard navigation for search results
    let selectedIndex = $state(0);
    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'Escape') {
            closeSearchModal();
        } else if (e.key === 'ArrowDown') {
            if ($searchResults.length > 0) {
                selectedIndex = (selectedIndex + 1) % $searchResults.length;
                scrollSelectedIntoView();
            }
        } else if (e.key === 'ArrowUp') {
            if ($searchResults.length > 0) {
                selectedIndex = (selectedIndex - 1 + $searchResults.length) % $searchResults.length;
                scrollSelectedIntoView();
            }
        } else if (e.key === 'Enter' && $searchResults.length > 0) {
            const selected = $searchResults[selectedIndex] || $searchResults[0];
            if (onNavigate) onNavigate();
            window.location.href = selected.path;
            closeSearchModal();
        }
    }

    // Scroll selected result into view
    function scrollSelectedIntoView() {
        setTimeout(() => {
            const el = document.querySelector('.search-result.selected');
            el?.scrollIntoView({ block: 'nearest' });
        }, 0);
    }

    // Handle click outside to close modal
    function handleClickOutside(e: MouseEvent) {
        if (showSearchModal && searchModalRef && !searchModalRef.contains(e.target as Node)) {
            closeSearchModal();
        }
    }

    // Handle global keyboard shortcuts
    function handleGlobalKeydown(e: KeyboardEvent) {
        // Ctrl+K or Cmd+K to open search modal
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            openSearchModal();
        }
    }

    // Add/remove global keyboard listener
    onMount(() => {
        document.addEventListener('keydown', handleGlobalKeydown);
        return () => {
            document.removeEventListener('keydown', handleGlobalKeydown);
        };
    });

    // Add/remove click outside listener when modal opens/closes
    $effect(() => {
        if (showSearchModal) {
            // Add a small delay to prevent the initial click from immediately closing the modal
            const timeoutId = setTimeout(() => {
                document.addEventListener('click', handleClickOutside);
            }, 100);

            return () => {
                clearTimeout(timeoutId);
                document.removeEventListener('click', handleClickOutside);
            };
        }
    });

    // React to search query changes
    $effect(() => {
        if (searchQuery.trim()) {
            const timeoutId = setTimeout(() => {
                performSearch(searchQuery);
                selectedIndex = 0;
            }, 100); // Reduced from 200ms to 100ms for faster response
            return () => clearTimeout(timeoutId);
        } else {
            searchResults.set([]);
            selectedIndex = 0;
        }
    });

    // Set context so child components can access the onNavigate function
    setContext('onNavigate', onNavigate);
    setContext('searchQuery', { get: () => searchQuery, set: (v: string) => searchQuery = v });
    setContext('searchResults', searchResults);
    setContext('showSearchModal', { get: () => showSearchModal, set: (v: boolean) => showSearchModal = v });

    let randomValue = $state(Math.random());
    afterNavigate(() => {
        // Generate a new random index on navigation
        randomValue = Math.random();
    });
    let randomLink = $derived.by(() => {
        const keys = Array.from(moduleCache.keys());
        const randomKey = keys[Math.floor(randomValue * keys.length)];
        return randomKey;
    });

</script>
{#if dev && false}
<!-- button to go to random page -->
<a
    href={prefix ? `${prefix}/${randomLink}` : `/${randomLink}`}
    onclick={() => {
        if (onNavigate) onNavigate();
    }}
    class="text-blue-500 hover:underline"
    aria-label="Go to random documentation page"
>
    <i class="fas fa-random"></i> Random Page
</a>

<WordCountDistributionDocs {allModules} {randomValue}></WordCountDistributionDocs>
{/if}

<nav class="summary-nav max-h-[calc(100vh-8rem)] overflow-y-auto pb-8">
    <!-- Search Button -->
    <div class="mb-6 p-2">
        <button
            onclick={openSearchModal}
            class="w-full px-4 py-3 text-left border border-gray-200 rounded-lg bg-white hover:border-gray-300 transition-colors duration-200 flex items-center gap-3 cursor-text"
        >
            <i class="fas fa-search text-gray-400 text-sm"></i>
            <span class="text-sm text-gray-500 flex-1">Search documentation...</span>
            <kbd class="hidden sm:inline-flex items-center px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded border border-gray-200">
                <span class="text-xs">⌘</span>K
            </kbd>
        </button>
    </div>

    <!-- Always show Summary Navigation -->
    <Summary/>
</nav>

<!-- Search Modal -->
{#if showSearchModal}
    <!-- Background overlay -->
    <div
        class="fixed inset-0 bg-black/25 z-40"
        onclick={closeSearchModal}
        onkeydown={(e) => { if (e.key === 'Escape') closeSearchModal(); }}
        role="button"
        tabindex="-1"
        aria-label="Close search modal"
    ></div>

    <div class="fixed top-20 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-2xl mx-4" bind:this={searchModalRef}>
        <div class="bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden">
            <!-- Modal Header -->
            <div class="border-b border-gray-200 p-4">
                <div class="flex items-center gap-3">
                    <i class="fas fa-search text-gray-400"></i>
                    <input
                        bind:value={searchQuery}
                        bind:this={searchInputRef}
                        onkeydown={handleKeydown}
                        placeholder="Search documentation..."
                        class="flex-1 bg-transparent text-lg outline-none text-gray-900 placeholder-gray-500"
                    />
                    <button onclick={closeSearchModal} class="text-gray-400 hover:text-gray-600" aria-label="Close search">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>

            <!-- Search Results -->
            <div class="max-h-96 overflow-y-auto">
                {#if searchQuery.trim() && $searchResults.length > 0}
                    <div class="p-2">
                        {#each $searchResults as result, i}
                            <a
                                href={result.path}
                                onclick={() => { if (onNavigate) onNavigate(); closeSearchModal(); }}
                                class="search-result block p-4 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0 {i === selectedIndex ? 'selected bg-blue-50 border-blue-200' : ''}"
                                tabindex="-1"
                                aria-selected={i === selectedIndex}
                            >
                                <div class="flex items-start gap-3">
                                    <i class="fas fa-file-text text-blue-500 text-sm mt-1"></i>
                                    <div class="flex-1 min-w-0">
                                        <h4 class="font-medium text-gray-900 mb-1">
                                            {result.title}
                                        </h4>
                                        <p class="text-sm text-gray-500 mb-2">
                                            {result.path === '/' ? 'Home' : result.path.replace(/^\//, '').replace(/\//g, ' › ')}
                                        </p>
                                        {#if result.excerpt}
                                            <div class="text-sm text-gray-600 leading-relaxed">
                                                {@html result.excerpt}
                                            </div>
                                        {/if}
                                    </div>
                                </div>
                            </a>
                        {/each}
                    </div>
                {:else if searchQuery.trim() && $searchResults.length === 0}
                    <div class="p-8 text-center">
                        <i class="fas fa-search text-gray-300 text-2xl mb-3 block"></i>
                        <p class="text-gray-500 mb-1">No results found for "{searchQuery}"</p>
                        <p class="text-sm text-gray-400">Try different keywords</p>
                    </div>
                {:else}
                    <div class="p-8 text-center">
                        <i class="fas fa-search text-gray-300 text-2xl mb-3 block"></i>
                        <p class="text-gray-500 mb-1">Start typing to search</p>
                        <p class="text-sm text-gray-400">Press <kbd class="px-2 py-1 bg-gray-100 rounded text-xs">Enter</kbd> to select first result</p>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{/if}
