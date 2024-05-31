<script lang="ts">
	import type { Device, Module, Tag } from '$lib/state';
	import type { Page } from '@sveltejs/kit';
	import { P } from 'flowbite-svelte';
	import { queryParam } from 'sveltekit-search-params';

	export let queryPrefix = '';
	export let target: Tag | Device | undefined;
	export let selfModules: Module[];
	export let page: Page;

	const moduleParam = queryParam('module');
	const configTargetParam = queryParam('config-target');

	const otherUrlParams = (searchParams: string) => {
		const params = new URLSearchParams(searchParams);
		params.delete('module');
		params.delete('config-target');
		return params.toString();
	};
</script>

<div class="flex gap-2 mb-2 ml-1">
	<slot name="icon" />
	<P>{target?.displayName}</P>
</div>
<div class="mb-4">
	{#each selfModules as module}
		<a
			href="/config?{otherUrlParams(
				page.url.search
			)}&module={module.type}&config-target={queryPrefix + target?.identifier}"
			class={`block p-2 rounded ${
				module.type === $moduleParam && queryPrefix + target?.identifier === $configTargetParam
					? 'bg-gray-200 dark:bg-gray-600'
					: 'hover:bg-gray-300 dark:hover:bg-gray-700'
			}`}
		>
			<P>{module.displayName}</P>
		</a>
	{/each}
</div>
