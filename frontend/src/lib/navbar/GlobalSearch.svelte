<script lang="ts">
	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import { Dropdown, DropdownItem, Search } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		globalState
	} from '$lib/state';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

	let search = $state('');
	let open = $state(false);

	const isSearched = (search: string, item: string) => {
		if (!search) {
			return true;
		}

		const searchKeys = search.trim().split(' ');
		return searchKeys.every((key) => item.toLowerCase().includes(key.toLowerCase()));
	};
</script>

<Search
	class="lg:w-64 xl:w-96 p-2 pl-8 "
	size="sm"
	bind:value={search}
	placeholder={$t('common.search')}
/>
<Dropdown
	class="lg:w-64 xl:w-96 flex flex-col overflow-y-auto h-full w-full text-sm relative gap-1 py-1"
	id="global-search-dropdown"
	bind:open
>
	{#each $globalState.tags as tag}
		{@const active =
			$globalNavSelectedTargetType === 'tag' &&
			$globalNavSelectedTag?.identifier === tag.identifier}
		{@const subpage = [
			'/configuration/edit',
			targetShouldShowVNC(tag, $globalState) ? '/configuration/vnc' : undefined
		].includes($page.url.pathname)
			? $page.url.pathname
			: '/configuration/edit'}
		{#if isSearched(search, tag.displayName)}
			<DropdownItem
				href={`${subpage}?${buildGlobalNavSearchParam($page.url.search, 'tag', tag.identifier)}`}
				class={`flex gap-2 p-1 hover:bg-gray-100 items-center rounded ${active ? 'text-primary-600 dark:text-primary-400 hover:text-primary-600' : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'}`}
				on:click={() => (open = false)}
			>
				<TagIcon size={'1rem'} class="min-w-4" />
				<span class="text-base truncate" title={tag.displayName}>{tag.displayName}</span>
			</DropdownItem>
		{/if}
	{/each}
	{#each $globalState.configs as config}
		{@const active =
			$globalNavSelectedTargetType === 'config' &&
			$globalNavSelectedConfig?.identifier === config.identifier}
		{@const subpage = [
			'/configuration/configuration-details',
			'/configuration/edit',
			targetShouldShowVNC(config, $globalState) ? '/configuration/vnc' : undefined,
			'/configuration/terminal'
		].includes($page.url.pathname)
			? $page.url.pathname
			: '/configuration/configuration-details'}
		{#if isSearched(search, config.displayName)}
			<DropdownItem
				href={`${subpage}?${buildGlobalNavSearchParam($page.url.search, 'config', config.identifier)}`}
				class={`flex gap-2 p-1 hover:bg-gray-100 items-center rounded ${active ? 'text-primary-600 dark:text-primary-400 hover:text-primary-600' : 'text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white'}`}
				on:click={() => (open = false)}
			>
				<FileCode size={'1rem'} class="min-w-4" />
				<span class="text-base truncate" title={config.displayName}>{config.displayName}</span>
			</DropdownItem>
		{/if}
	{/each}
</Dropdown>
