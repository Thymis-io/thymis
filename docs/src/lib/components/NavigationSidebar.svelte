<script lang="ts">
    import Summary from "$lib/docs/SUMMARY.md";
    import { setContext } from 'svelte';

    interface Props {
        onNavigate?: () => void;
    }

    let { onNavigate }: Props = $props();

    // Set context so child components can access the onNavigate function
    setContext('navigation', { onNavigate });
</script>

<nav class="summary-nav">
    <Summary/>
</nav>
