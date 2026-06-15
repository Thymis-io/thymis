<script lang="ts">
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		title?: string;
		subtitle?: string;
		titleExtra?: Snippet;
		actions?: Snippet;
		children?: Snippet;
	}

	let { title, subtitle, titleExtra, actions, children }: Props = $props();
</script>

<PageHead {title} {subtitle} {actions}>
	{#snippet children()}
		{@render titleExtra?.()}
	{/snippet}
</PageHead>

{@render children?.()}
