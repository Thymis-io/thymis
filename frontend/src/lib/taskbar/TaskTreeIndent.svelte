<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		depth: number;
		children: Snippet;
	}

	let { depth, children }: Props = $props();
</script>

<div class="flex items-center gap-1.5" style="padding-left: {depth * 1.25}rem">
	{#if depth >= 1}
		<span class="tree-guide" aria-hidden="true">└</span>
	{/if}
	{@render children()}
</div>

<style lang="postcss">
	.tree-guide {
		color: var(--ds-text-mute);
		flex-shrink: 0;
	}
</style>
