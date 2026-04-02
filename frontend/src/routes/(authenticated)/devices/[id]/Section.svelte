<script lang="ts">
	interface Props {
		title: string;
		class?: string;
		children?: import('svelte').Snippet;
	}
	let { title, class: className = '', children }: Props = $props();
</script>

<div
	class="w-full rounded-lg border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-800 sm:p-6 {className}"
>
	<h2 class="mb-4 text-xl font-semibold">{title}</h2>
	{@render children?.()}
</div>
