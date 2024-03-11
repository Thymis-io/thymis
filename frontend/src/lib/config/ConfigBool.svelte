<script lang="ts">
	import { Toggle } from 'flowbite-svelte';
	export let name: string;
	export let value: boolean | undefined = false;
	export let change: (value: boolean) => void = () => {};

	let changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).checked);
	};
</script>

<Toggle class="mt-1.5" size="small" {name} checked={value} on:change={changeInternal} />
