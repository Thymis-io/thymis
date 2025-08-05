<script lang="ts">
    let { currentPath } = $props<{ currentPath: string }>();

    const pathSegments = $derived(() => {
        if (!currentPath || currentPath === 'index') return [{ name: 'Home', path: '/index' }];

        const segments = currentPath.split('/');
        const breadcrumbs = [{ name: 'Home', path: '/index' }];

        let accumulatedPath = '';
        for (const segment of segments) {
            accumulatedPath += segment;
            const name = segment.charAt(0).toUpperCase() + segment.slice(1).replace(/_/g, ' ');
            breadcrumbs.push({ name, path: `/${accumulatedPath}` });
            accumulatedPath += '/';
        }

        return breadcrumbs;
    });
</script>

<nav class="flex items-center space-x-2 text-sm text-gray-600 mb-6">
    {#each pathSegments() as segment, index}
        {#if index > 0}
            <span class="text-gray-400">/</span>
        {/if}
        <a
            href={segment.path}
            class="hover:text-gray-900 transition-colors {index === pathSegments().length - 1 ? 'font-medium text-gray-900' : ''}"
        >
            {segment.name}
        </a>
    {/each}
</nav>
