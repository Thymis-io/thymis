<script lang="ts">
    import { setContext } from 'svelte';
    const Summary = import.meta.glob('../docs/SUMMARY.md', { eager: true })['../docs/SUMMARY.md'].default;

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
