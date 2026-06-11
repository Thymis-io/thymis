<script lang="ts">
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		title?: string;
		subtitle?: string;
		/** Title-adjacent content (badges, edit buttons) — rendered next to the title. */
		titleExtra?: Snippet;
		/** Page-level action buttons — rendered on the right, before the global deploy actions. */
		actions?: Snippet;
		/** Page body. */
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
