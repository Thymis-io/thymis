<script lang="ts">
	export let title: string;

	let className = '';
	export { className as class };
</script>

<div class={className}>
	<h1 class="text-1xl font-bold mb-2">{title}</h1>
	<div class="flex flex-col gap-2">
		<slot />
	</div>
</div>
