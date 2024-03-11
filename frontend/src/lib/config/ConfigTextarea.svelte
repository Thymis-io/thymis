<script lang="ts">
	import { Textarea } from 'flowbite-svelte';
	export let placeholder: string | null;
	export let value: unknown;

	export let change: (value: string) => void = () => {};

	const changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).value);
	};
</script>

<Textarea {placeholder} on:change={changeInternal}>
	{value || ''}
</Textarea>
