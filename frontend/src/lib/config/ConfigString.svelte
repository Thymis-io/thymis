<script lang="ts">
	export let placeholder: string | null;
	export let value: unknown;
</script>

<input
	class="w-full rounded-md bg-transparent border border-blue-gray-200 border-t-transparent outline outline-1 outline-secondary-400/70 p-1"
	type="text"
	{placeholder}
	bind:value
/>
