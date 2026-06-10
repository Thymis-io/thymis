<script lang="ts">
	interface Props {
		title: string;
		class?: string;
		header?: import('svelte').Snippet;
		children?: import('svelte').Snippet;
	}

	let { title, class: className = '', header, children }: Props = $props();
</script>

<div class="ds-card flex flex-col {className}">
	<div class="ds-card-head">
		<h2 class="ds-card-title">{title}</h2>
		{@render header?.()}
	</div>
	<div class="ds-card-pad flex flex-1 flex-col gap-2">
		{@render children?.()}
	</div>
</div>
