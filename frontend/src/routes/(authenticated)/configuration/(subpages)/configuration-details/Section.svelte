<script lang="ts">
	interface Props {
		title: string;
		class?: string;
		header?: import('svelte').Snippet;
		children?: import('svelte').Snippet;
	}

	let { title, class: className = '', header, children }: Props = $props();
</script>

<div class={className}>
	<div class="flex items-center gap-2 mb-2">
		<h1 class="text-1xl font-bold">
			{title}
		</h1>
		{@render header?.()}
	</div>
	<div class="flex flex-col gap-2">
		{@render children?.()}
	</div>
</div>
