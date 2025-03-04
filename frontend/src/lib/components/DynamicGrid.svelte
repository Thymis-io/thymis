<script lang="ts">
	interface Props {
		columns: number;
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { columns, class: className = '', children }: Props = $props();
</script>

<div class="grid {className}" style="grid-template-columns: repeat({columns}, minmax(0, 1fr));">
	{@render children?.()}
</div>
