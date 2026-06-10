<script lang="ts">
	interface Props {
		title: string;
		class?: string;
		children?: import('svelte').Snippet;
	}
	let { title, class: className = '', children }: Props = $props();
</script>

<div class="ds-card flex flex-col w-full {className}">
	<div class="ds-card-head">
		<h2 class="ds-card-title">{title}</h2>
	</div>
	<div class="ds-card-pad flex-1">
		{@render children?.()}
	</div>
</div>
