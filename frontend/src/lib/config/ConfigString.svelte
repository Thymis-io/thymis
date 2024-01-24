<script lang="ts">
	export let placeholder: string | null;
	export let value: unknown;

	export let onChange: (value: string) => void = () => {};

	let change = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};
</script>

<input
	class="w-full rounded-md bg-transparent border border-blue-gray-200 border-t-transparent outline outline-1 outline-secondary-400/70 p-1"
	type="text"
	{placeholder}
	value={value || ''}
	on:change={change}
/>
