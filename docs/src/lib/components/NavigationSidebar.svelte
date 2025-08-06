<script lang="ts">
    import { setContext } from 'svelte';
    import Summary from '../docs/SUMMARY.md';
	import { writable } from 'svelte/store';

    interface Props {
        onNavigate?: () => void;
        currentPath?: string;
    }

    let { onNavigate, currentPath = '' }: Props = $props();

    // Set context so child components can access the onNavigate function and currentPath
    setContext('onNavigate', onNavigate);

    let currentPathStore = writable(currentPath);
    // Update the currentPath store whenever currentPath changes
    $effect(() => {
        currentPathStore.set(currentPath);
    });
    setContext('currentPath', currentPathStore);
</script>

<nav class="summary-nav">
    <Summary/>
</nav>
