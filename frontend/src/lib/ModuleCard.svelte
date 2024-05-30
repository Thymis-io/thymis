<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card, Button, P } from 'flowbite-svelte';
	import type { ModuleSettings, Module } from './state';
	import { page } from '$app/stores';
	import { queryParam } from 'sveltekit-search-params';

	export let module: Module;
	export let installed: boolean;
	export let addModule: (module: ModuleSettings | Module) => void;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	const otherUrlParams = (searchParams: string) => {
		const params = new URLSearchParams(searchParams);
		params.delete('module');
		return params.toString();
	};
</script>

<Card class="w-48 h-48 !p-2 flex justify-between items-center">
	<P class="font-bold">{module.displayName}</P>
	<img class="h-20 w-20 object-scale-down" src={module.icon ?? '/favicon.png'} alt="icon" />
	{#if installed}
		<Button
			size="xs"
			class="!w-28"
			href="/config?{otherUrlParams(
				$page.url.search
			)}&module={module.type}&config-target=self-{$tagParam ?? $deviceParam}"
		>
			{$t('config.configure')}
		</Button>
	{:else}
		<Button size="xs" class="!w-28" on:click={() => addModule(module)}>
			{$t('config.install')}
		</Button>
	{/if}
</Card>
