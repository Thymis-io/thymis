<script lang="ts">
    import { goto } from '$app/navigation';

    let { allModules } = $props<{ allModules: string[] }>();

    let searchQuery = $state('');
    let isOpen = $state(false);

    const filteredModules = $derived(() => {
        if (!searchQuery.trim()) return [];

        return allModules
            .filter((module: string) =>
                module.toLowerCase().includes(searchQuery.toLowerCase()) ||
                module.split('/').some((segment: string) =>
                    segment.toLowerCase().includes(searchQuery.toLowerCase())
                )
            )
            .slice(0, 8); // Limit to 8 results
    });

    function handleKeydown(event: KeyboardEvent) {
        if (event.key === 'Escape') {
            isOpen = false;
            searchQuery = '';
        }
    }

    function selectResult(module: string) {
        goto(`/${module}`);
        isOpen = false;
        searchQuery = '';
    }
</script>

<div class="relative mb-6">
    <div class="relative">
        <input
            type="text"
            placeholder="Search documentation..."
            bind:value={searchQuery}
            onfocus={() => isOpen = true}
            onblur={() => setTimeout(() => isOpen = false, 200)}
            onkeydown={handleKeydown}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <div class="absolute inset-y-0 right-0 flex items-center pr-3">
            <svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
        </div>
    </div>

    {#if isOpen && filteredModules.length > 0}
        <div class="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
            {#each filteredModules as module}
                <button
                    type="button"
                    onclick={() => selectResult(module)}
                    class="w-full px-4 py-2 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none first:rounded-t-lg last:rounded-b-lg"
                >
                    <div class="text-sm font-medium text-gray-900">
                        {module.split('/').pop() || module}
                    </div>
                    <div class="text-xs text-gray-500">
                        {module}
                    </div>
                </button>
            {/each}
        </div>
    {/if}
</div>
