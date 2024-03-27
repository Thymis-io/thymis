<script lang="ts">
	import { Card, Button, P } from 'flowbite-svelte';
	import type { Module } from './state';
	import { page } from '$app/stores';

	export let module: Module;
	export let installed: boolean;
	export let addModule: (module: Module) => void;

	$: moduleName = module.name.charAt(0).toUpperCase() + module.name.slice(1);

	const otherUrlParams = (searchParams: string) => {
		const params = new URLSearchParams(searchParams);
		params.delete('module');
		return params.toString();
	};

	const icon = () => {
		return module.icon ?? '/favicon.png';
	};
</script>

<Card class="w-48 h-48 !p-2 flex justify-between items-center">
	<P class="font-bold">{moduleName}</P>
	<img class="h-20 w-20 object-scale-down" src={icon()} alt="icon" />
	{#if installed}
		<Button
			size="xs"
			class="!w-28"
			href="/config?{otherUrlParams($page.url.search)}&module={module.type}"
		>
			Configure
		</Button>
	{:else}
		<Button size="xs" class="!w-28" on:click={() => addModule(module)}>Install</Button>
	{/if}
</Card>
