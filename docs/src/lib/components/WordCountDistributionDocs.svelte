<script lang="ts">
    import { setContext, onMount, getContext } from 'svelte';
    import { writable } from 'svelte/store';
    import { Index } from 'flexsearch';
    import { afterNavigate } from '$app/navigation';
	import A from './summary/a.svelte';


    interface Props {
        allModules?: Record<string, any> | Array<{path: string, module: any}>; // Support both formats
        randomValue?: number; // Optional random value for testing
    }

    let { allModules = {}, randomValue }: Props = $props();

    // we want to show a progress bar for docs pages during the writing process
    // We will count words in the docs page
    // 0-25: stub
    // 25-100: very short
    // 100-250: short
    // 250-500: medium
    // 500-1000: long
    // 1000+: very long
    // for each of the modules (from allModules) we will count the words in the content
    // contents are in module.metadata.contents
    let wordCounts = $state({});
    let categorizedWordCounts = $state({
        stub: 0,
        veryShort: 0,
        short: 0,
        medium: 0,
        long: 0,
        veryLong: 0
    });
    let randomPageForCategories: Record<string, string> = $state({});
    $effect(() => {
        if (allModules) {
            if (Array.isArray(allModules)) {
                allModules.forEach(({ path, module }) => {
                    const cleanPath = path.replace(/^\.\//, '').replace(/\.md$/, '');
                    const fullContent = module?.metadata?.contents || module?.metadata?.fm?.contents || '';
                    if (fullContent && !cleanPath.includes('SUMMARY') && !path.includes('SUMMARY.md')) {
                        const wordCount = fullContent.split(/\s+/).filter(Boolean).length;
                        wordCounts[cleanPath] = wordCount; // Use object notation for direct assignment
                    }
                });
            } else {
                Object.entries(allModules).forEach(([path, module]) => {
                    const fullContent = module?.metadata?.contents || module?.metadata?.fm?.contents || '';
                    if (fullContent && !path.includes('SUMMARY') && !path.includes('SUMMARY.md')) {
                        const wordCount = fullContent.split(/\s+/).filter(Boolean).length;
                        wordCounts[path] = wordCount; // Use object notation for direct assignment
                    }
                });
            }
        }

        const start = {
            stub: 0,
            veryShort: 0,
            short: 0,
            medium: 0,
            long: 0,
            veryLong: 0
        };


        for (const [path, count] of Object.entries(wordCounts)) {
            if (count <= 25) {
                start.stub++;
            } else if (count <= 100) {
                start.veryShort++;
            } else if (count <= 250) {
                start.short++;
            } else if (count <= 500) {
                start.medium++;
            } else if (count <= 1000) {
                start.long++;
            } else {
                start.veryLong++;
            }
        }

        // only set if different to avoid unnecessary updates
        for (const [key, value] of Object.entries(start)) {
            const typedKey = key as keyof typeof categorizedWordCounts;
            if (categorizedWordCounts[typedKey] !== value) {
                categorizedWordCounts[typedKey] = value;
            }
        }

        // Select random pages for each category
        // use random value and multiply by the number of pages in each category
        // choose kth page in the category
        const pagesByCategory: Record<string, string> = {
            stub: [],
            veryShort: [],
            short: [],
            medium: [],
            long: [],
            veryLong: []
        };
        for (const [path, count] of Object.entries(wordCounts)) {
            if (count <= 25) {
                pagesByCategory.stub.push(path);
            } else if (count <= 100) {
                pagesByCategory.veryShort.push(path);
            } else if (count <= 250) {
                pagesByCategory.short.push(path);
            } else if (count <= 500) {
                pagesByCategory.medium.push(path);
            } else if (count <= 1000) {
                pagesByCategory.long.push(path);
            } else {
                pagesByCategory.veryLong.push(path);
            }
        }
        const thisRandom = {};
        // Generate random pages for each category
        for (const [category, pages] of Object.entries(pagesByCategory)) {
            if (pages.length > 0) {
                const randomIndex = Math.floor(randomValue * pages.length);
                thisRandom[category] = pages[randomIndex];
            } else {
                thisRandom[category] = null; // No pages in this category
            }
        }
        // apply if and only if different
        for (const [key, value] of Object.entries(thisRandom)) {
            if (randomPageForCategories[key] !== value) {
                randomPageForCategories[key] = value;
            }
        }

        // Log the word counts for debugging
        console.log('Word Counts:', wordCounts);
        console.log('Categorized Word Counts:', categorizedWordCounts);
        console.log('Random Pages by Category:', thisRandom);
    });

    // colors:

const colorScales = {
    // Traditional Red-to-Green (completion)
    redGreen: {
        stub: '#ef4444',      // red-500
        veryShort: '#f97316', // orange-500
        short: '#eab308',     // yellow-500
        medium: '#84cc16',    // lime-500
        long: '#22c55e',      // green-500
        veryLong: '#16a34a'   // green-600
    },

    // Cool Blues (professional)
    blueScale: {
        stub: '#f1f5f9',      // slate-50
        veryShort: '#cbd5e1',  // slate-300
        short: '#94a3b8',      // slate-400
        medium: '#64748b',     // slate-500
        long: '#475569',       // slate-600
        veryLong: '#334155'    // slate-700
    },

    // Warm Sunset (vibrant)
    sunset: {
        stub: '#fef3c7',      // amber-100
        veryShort: '#fde68a', // amber-200
        short: '#f59e0b',     // amber-500
        medium: '#d97706',    // amber-600
        long: '#ea580c',      // orange-600
        veryLong: '#dc2626'   // red-600
    },

    // Purple to Pink (modern)
    purplePink: {
        stub: '#fdf4ff',      // fuchsia-50
        veryShort: '#f0abfc', // fuchsia-300
        short: '#e879f9',     // fuchsia-400
        medium: '#d946ef',    // fuchsia-500
        long: '#c026d3',      // fuchsia-600
        veryLong: '#a21caf'   // fuchsia-700
    },

    // GitHub-style Green (familiar to developers)
    github: {
        stub: '#ebedf0',      // Very light gray
        veryShort: '#c6e48b', // Light green
        short: '#7bc96f',     // Medium light green
        medium: '#239a3b',    // Medium green
        long: '#196127',      // Dark green
        veryLong: '#0d4429'   // Very dark green
    },

    // Ocean (calming blues/teals)
    ocean: {
        stub: '#f0fdfa',      // emerald-50
        veryShort: '#a7f3d0', // emerald-200
        short: '#6ee7b7',     // emerald-300
        medium: '#10b981',    // emerald-500
        long: '#059669',      // emerald-600
        veryLong: '#047857'   // emerald-700
    },

    // Monochrome (grayscale)
    monochrome: {
        stub: '#f8fafc',      // slate-50
        veryShort: '#e2e8f0', // slate-200
        short: '#cbd5e1',     // slate-300
        medium: '#64748b',    // slate-500
        long: '#475569',      // slate-600
        veryLong: '#1e293b'   // slate-800
    },

    // Fire (red/orange gradient)
    fire: {
        stub: '#fef2f2',      // red-50
        veryShort: '#fecaca', // red-200
        short: '#f87171',     // red-400
        medium: '#ef4444',    // red-500
        long: '#dc2626',      // red-600
        veryLong: '#991b1b'   // red-800
    },

    // Nature (earth tones)
    nature: {
        stub: '#fefce8',      // yellow-50
        veryShort: '#bef264', // lime-300
        short: '#84cc16',     // lime-500
        medium: '#65a30d',    // lime-600
        long: '#166534',      // green-800
        veryLong: '#14532d'   // green-900
    },

    // Cyberpunk (neon-inspired)
    cyberpunk: {
        stub: '#1e1b4b',      // indigo-900
        veryShort: '#3730a3', // indigo-700
        short: '#6366f1',     // indigo-500
        medium: '#8b5cf6',    // violet-500
        long: '#a855f7',      // purple-500
        veryLong: '#ec4899'   // pink-500
    }
};

// Choose your preferred scale
let selectedColorScale = $state(colorScales.github); // Change this to any scale above



// Type-safe function to get color for category
function getColorForCategory(category: string): string {
    const categoryKey = category as keyof typeof selectedColorScale;
    let color = selectedColorScale[categoryKey] || selectedColorScale.stub;
    return color;
}

// Word count ranges for detailed breakdown
const wordRanges: Record<string, string> = {
    stub: '0-25',
    veryShort: '26-100',
    short: '101-250',
    medium: '251-500',
    long: '501-1000',
    veryLong: '1000+'
};

// Calculate percentages and display names for categories
let categoryStats = $derived.by(() => {
    const totalPages = Object.keys(wordCounts).length;
    return Object.entries(categorizedWordCounts).map(([category, count]) => {
        const percentage = totalPages > 0 ? (count / totalPages * 100) : 0;
        const displayName = category === 'veryShort' ? 'very short' : category === 'veryLong' ? 'very long' : category;
        return {
            category,
            count,
            percentage,
            displayName,
            color: getColorForCategory(category),
            wordRange: wordRanges[category]
        };
    });
});

let nonStubPercent = $derived.by(() => {
    const totalPages = Object.keys(wordCounts).length;
    const stubStat = categoryStats.find(stat => stat.category === 'stub');
    const stubCount = stubStat ? stubStat.count : 0;
    const nonStub = totalPages > 0 ? totalPages - stubCount : 0;
    return totalPages > 0 ? (nonStub / totalPages * 100) : 0;
});

// when clicking on a category, I want to show a random page from that category
// randomValue is 0-1
// let randomPagesForCategories: Record<string, string[]> = $derived.by(() => {
//     const categories = Object.keys(categorizedWordCounts);
//     const randomPages: Record<string, string[]> = {};
//     for (const category of categories) {
//         randomPages[category] = [];
//         for (const [path, count] of Object.entries(wordCounts)) {
//             if (count > 0 && path.includes(category)) {
//                 randomPages[category].push(path);
//             }
//         }
//     }
//     console.log('Random Pages by Category:', randomPages);
//     return randomPages;
// });

$effect(() => {
    // Log the random pages for debugging
    console.log('Random Pages by Category:', randomPageForCategories);
});

</script>

<!-- widget for word count distribution -->
<div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
    <h3 class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <i class="fas fa-chart-bar text-gray-500"></i>
        Documentation Progress
    </h3>

    <!-- Summary stats -->
    <div class="mb-4 grid grid-cols-2 gap-2 text-xs">
        <div class="text-gray-600">
            <span class="font-medium">{Object.keys(wordCounts).length}</span> pages
        </div>
        <div class="text-gray-600">
            <span class="font-medium">{Object.values(wordCounts).reduce((a, b) => a + b, 0)}</span> words
        </div>
    </div>

    <!-- Stacked progress bar showing overall distribution -->
    <div class="mb-4">
        <div class="flex text-xs text-gray-600 mb-1 justify-between">
            <span>Overall Progress</span>
            <span>{Object.keys(wordCounts).length} pages</span>
        </div>
        <div class="h-3 bg-gray-200 rounded-full overflow-hidden flex flex-row-reverse">
            {#each [...categoryStats] as stat}
                {#if stat.percentage > 0}
                    <div
                        class="h-full transition-all duration-500 ease-out"
                        style="width: {stat.percentage}%; background-color: {stat.color}"
                        title="{stat.displayName}: {stat.count} pages ({stat.percentage.toFixed(1)}%)"
                    ></div>
                {/if}
            {/each}
        </div>
        <div class="flex justify-end text-xs text-gray-500 mt-1">
            <span class="font-semibold text-green-700">{nonStubPercent.toFixed(1)}%</span>
            <span class="ml-1">non-stub</span>
        </div>
    </div>

    <!-- Individual progress bars for each category -->
    <div class="space-y-2">
        {#each categoryStats as stat}
        <A href={randomPageForCategories[stat.category] || '#'}>
            <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2 min-w-0 flex-1">
                    <div
                        class="w-2 h-2 rounded-full flex-shrink-0"
                        style="background-color: {stat.color}"
                    ></div>
                    <span class="text-gray-600 capitalize truncate">{stat.displayName}</span>
                    <span class="text-gray-400">({stat.wordRange})</span>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                    <span class="text-gray-500 font-mono">{stat.count}</span>
                    <span class="text-gray-400">({stat.percentage.toFixed(0)}%)</span>
                </div>
            </div>
            <div class="h-1.5 rounded-full overflow-hidden"
                style="background-color: {stat.category === 'stub' && ['#ebedf0','#f1f5f9','#fef3c7','#fdf4ff','#f0fdfa','#f8fafc','#fef2f2','#fefce8'].includes(stat.color.toLowerCase()) ? '#222' : '#e5e7eb'}">
                <div
                    class="h-full transition-all duration-500 ease-out rounded-full"
                    style="width: {Math.max(stat.percentage, stat.count > 0 ? 2 : 0)}%; background-color: {stat.color}"
                ></div>
            </div>
        </A>
        {/each}
    </div>

    <!-- Alternative stacked bar view -->
    <div class="mt-4 pt-3 border-t border-gray-200">
        <details class="group">
            <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700 transition-colors mb-2">
                <span class="inline-flex items-center gap-1">
                    <i class="fas fa-layer-group group-open:rotate-180 transition-transform"></i>
                    Detailed breakdown
                </span>
            </summary>
            <div class="mt-2 space-y-3">
                <!-- Category distribution with word count ranges -->
                <div class="grid grid-cols-3 gap-2 text-xs">
                    {#each categoryStats as stat}
                        <A href={randomPageForCategories[stat.category] || '#'}>
                            <div class="p-2 rounded border border-gray-200 bg-white">
                                <div class="flex items-center gap-1 mb-1">
                                    <div
                                        class="w-2 h-2 rounded-full flex-shrink-0"
                                        style="background-color: {stat.color}"
                                    ></div>
                                    <span class="font-medium capitalize text-gray-700 text-xs">{stat.displayName}</span>
                                </div>
                                <div class="text-gray-500 text-xs font-mono">{wordRanges[stat.category]} words</div>
                                <div class="text-gray-700 font-semibold">{stat.count} pages</div>
                            </div>
                        </A>
                    {/each}
                </div>
            </div>
        </details>
    </div>

    <!-- Legend explaining word count ranges -->
    <div class="mt-3 pt-3 border-t border-gray-200">
        <details class="group">
            <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700 transition-colors">
                <span class="inline-flex items-center gap-1">
                    <i class="fas fa-info-circle group-open:rotate-180 transition-transform"></i>
                    Word count ranges
                </span>
            </summary>
            <div class="mt-2 space-y-1 text-xs text-gray-500 pl-4">
                <div><span class="font-mono">0-25:</span> Stub</div>
                <div><span class="font-mono">26-100:</span> Very short</div>
                <div><span class="font-mono">101-250:</span> Short</div>
                <div><span class="font-mono">251-500:</span> Medium</div>
                <div><span class="font-mono">501-1000:</span> Long</div>
                <div><span class="font-mono">1000+:</span> Very long</div>
            </div>
        </details>
    </div>

    <!-- Color scheme selector -->
    <div class="mt-3 pt-3 border-t border-gray-200">
        <details class="group">
            <summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700 transition-colors">
                <span class="inline-flex items-center gap-1">
                    <i class="fas fa-palette group-open:rotate-180 transition-transform"></i>
                    Color scheme
                </span>
            </summary>
            <div class="mt-2 grid grid-cols-2 gap-1">
                {#each Object.entries(colorScales) as [scaleName, scale]}
                    <button
                        onclick={() => selectedColorScale = scale}
                        class="text-xs px-2 py-1 rounded border transition-colors text-left
                               {selectedColorScale === scale
                                 ? 'bg-blue-50 border-blue-200 text-blue-700'
                                 : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'}"
                    >
                        <div class="flex items-center gap-1">
                            <div class="flex gap-0.5">
                                {#each Object.values(scale) as color}
                                    <div class="w-1.5 h-1.5 rounded-full" style="background-color: {color}"></div>
                                {/each}
                            </div>
                            <span class="capitalize text-xs">
                                {scaleName.replace(/([A-Z])/g, ' $1').toLowerCase()}
                            </span>
                        </div>
                    </button>
                {/each}
            </div>
        </details>
    </div>
</div>
