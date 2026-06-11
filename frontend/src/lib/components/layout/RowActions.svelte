<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		/** Alignment of the action group within the cell (defaults to right). */
		align?: 'left' | 'right' | 'center';
		children?: Snippet;
	}

	let { align = 'right', children }: Props = $props();

	let justify = $derived(
		align === 'left' ? 'justify-start' : align === 'center' ? 'justify-center' : 'justify-end'
	);
</script>

<div class="flex {justify} gap-2">
	{@render children?.()}
</div>
