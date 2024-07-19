<script lang="ts">
	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import { Button, Dropdown, DropdownItem, Search } from 'flowbite-svelte';
	import ChevronDownSolid from 'flowbite-svelte-icons/ChevronDownSolid.svelte';
	import { page } from '$app/stores';
	import { globalNavSelectedDevice, globalNavSelectedTag, state, type State } from '../state';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';

	let search = '';

	const isSearched = (search: string, item: string) => {
		if (!search) {
			return true;
		}

		const searchKeys = search.trim().split(' ');
		return searchKeys.every((key) => item.toLowerCase().includes(key.toLowerCase()));
	};
</script>

<Button class="w-full flex justify-between">
	<div class="flex gap-2">
		{#if $globalNavSelectedTag}
			<TagIcon size={20} /> {$globalNavSelectedTag?.displayName}
		{:else if $globalNavSelectedDevice}
			<HardDrive size={20} /> {$globalNavSelectedDevice?.displayName}
		{:else}
			{$t('common.no-tag-or-device-selected')}
		{/if}
	</div>
	<ChevronDownSolid class="h-4 ms-2 text-white dark:text-white" /></Button
>
<Dropdown class="overflow-y-auto px-3 pb-3 text-sm max-h-96">
	<div slot="header" class="p-3">
		<Search size="md" bind:value={search} placeholder={$t('common.search')} />
	</div>
	{#each $state.tags as tag}
		{#if isSearched(search, tag.displayName)}
			<DropdownItem
				href={`?${buildGlobalNavSearchParam($page.url.search, 'tag', tag.identifier)}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<TagIcon />
				{tag.displayName}
			</DropdownItem>
		{/if}
	{/each}
	{#each $state.devices as device}
		{#if isSearched(search, device.displayName)}
			<DropdownItem
				href={`?${buildGlobalNavSearchParam($page.url.search, 'device', device.identifier)}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<HardDrive />
				{device.displayName}
			</DropdownItem>
		{/if}
	{/each}
</Dropdown>
