<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		class?: string;
		/** Extra content in the card header, right of the title (badges, controls). */
		header?: Snippet;
		children?: Snippet;
	}

	let { title, class: className = '', header, children }: Props = $props();
</script>

<div class="ds-card flex w-full flex-col {className}">
	<div class="ds-card-head">
		<h2 class="ds-card-title">{title}</h2>
		{@render header?.()}
	</div>
	<div class="ds-card-pad flex flex-1 flex-col gap-2">
		{@render children?.()}
	</div>
</div>
