<script lang="ts">
	interface Props {
		title: string;
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { title, class: className = '', children }: Props = $props();
</script>

<div class={className}>
	<h1 class="text-1xl font-bold mb-2">{title}</h1>
	<div class="flex flex-col gap-2">
		{@render children?.()}
	</div>
</div>
