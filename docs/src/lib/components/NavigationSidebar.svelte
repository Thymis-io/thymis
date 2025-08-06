<script lang="ts">
    import { setContext } from 'svelte';
    const Summary = import.meta.glob('../docs/SUMMARY.md', { eager: true })['../docs/SUMMARY.md'].default;

    interface Props {
        onNavigate?: () => void;
        currentPath?: string;
    }

    let { onNavigate, currentPath = '' }: Props = $props();

    // Set context so child components can access the onNavigate function and currentPath
    setContext('navigation', { onNavigate, currentPath });
</script>

<nav class="summary-nav">
    <Summary/>
</nav>
