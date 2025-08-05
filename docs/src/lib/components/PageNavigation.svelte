<script lang="ts">
    let { allModules, currentPath } = $props<{ allModules: string[]; currentPath: string }>();

    const moduleIndex = $derived(() => {
        const index = allModules.findIndex((module: string) => module === currentPath);
        return index;
    });

    const previousModule = $derived(() => {
        const index = moduleIndex();
        return index > 0 ? allModules[index - 1] : null;
    });

    const nextModule = $derived(() => {
        const index = moduleIndex();
        return index >= 0 && index < allModules.length - 1 ? allModules[index + 1] : null;
    });

    function formatModuleName(modulePath: string | null): string {
        if (!modulePath || typeof modulePath !== 'string') return '';

        return modulePath
            .split('/')
            .map(part => part.charAt(0).toUpperCase() + part.slice(1).replace(/_/g, ' '))
            .join(' / ');
    }
</script>

{#if previousModule || nextModule}
    <div class="border-t border-gray-200 mt-12 pt-8">
        <div class="flex justify-between items-center">
            {#if previousModule}
                <a
                    href="/{previousModule}"
                    class="flex items-center text-blue-600 hover:text-blue-800 group"
                >
                    <svg class="w-4 h-4 mr-2 transition-transform group-hover:-translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                    </svg>
                    <div class="text-left">
                        <div class="text-xs text-gray-500 uppercase tracking-wide">Previous</div>
                        <div class="font-medium">{formatModuleName(previousModule)}</div>
                    </div>
                </a>
            {:else}
                <div></div>
            {/if}

            {#if nextModule}
                <a
                    href="/{nextModule}"
                    class="flex items-center text-blue-600 hover:text-blue-800 group text-right"
                >
                    <div class="text-right">
                        <div class="text-xs text-gray-500 uppercase tracking-wide">Next</div>
                        <div class="font-medium">{formatModuleName(nextModule)}</div>
                    </div>
                    <svg class="w-4 h-4 ml-2 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                </a>
            {/if}
        </div>
    </div>
{/if}
