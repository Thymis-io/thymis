<script lang="ts">
	export let placeholder: string | null;
	export let value: unknown;

	export let change: (value: string) => void = () => {};

	const changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).value);
	};
</script>

<textarea
	class="w-full rounded-md bg-transparent border border-blue-gray-200 border-t-transparent outline outline-1 outline-secondary-400/70 p-1"
	{placeholder}
	on:change={changeInternal}>{value || ''}</textarea
>
