<script lang="ts">
	import { Input } from 'flowbite-svelte';
	export let placeholder: string | null;
	export let value: unknown;

	export let change: (value: string) => void = () => {};

	let changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).value);
	};
</script>

<Input type="text" {placeholder} value={value || ''} on:change={changeInternal} />
