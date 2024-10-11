<script lang="ts">
	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import { Button, Dropdown, DropdownItem, Search } from 'flowbite-svelte';
	import ChevronDownOutline from 'flowbite-svelte-icons/ChevronDownOutline.svelte';
	import { page } from '$app/stores';
	import {
		globalNavSelectedDevice,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '../state';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';

	let search = '';
	let open = false;

	const isSearched = (search: string, item: string) => {
		if (!search) {
			return true;
		}

		const searchKeys = search.trim().split(' ');
		return searchKeys.every((key) => item.toLowerCase().includes(key.toLowerCase()));
	};
</script>

<Button class="w-full flex justify-between p-3">
	<div class="flex gap-2 items-center">
		{#if $globalNavSelectedTag}
			<TagIcon size={20} />
			<span class="text-base">{$globalNavSelectedTag?.displayName}</span>
		{:else if $globalNavSelectedDevice}
			<HardDrive size={20} />
			<span class="text-base">{$globalNavSelectedDevice?.displayName}</span>
		{:else}
			{$t('common.no-tag-or-device-selected')}
		{/if}
	</div>
	<ChevronDownOutline class="h-4 ms-2 text-white dark:text-white" /></Button
>
<Dropdown
	class="overflow-y-auto px-3 h-60 text-sm relative"
	containerClass="z-50 left-4 right-4 flex flex-col whitespace-nowrap"
	strategy="absolute"
	bind:open
>
	<div slot="header" class="p-3 pb-0">
		<Search size="md" bind:value={search} placeholder={$t('common.search')} />
	</div>
	{#each $state.tags as tag}
		{@const active =
			$globalNavSelectedTargetType === 'tag' &&
			$globalNavSelectedTag?.identifier === tag.identifier}
		{#if isSearched(search, tag.displayName)}
			<DropdownItem
				href={`?${buildGlobalNavSearchParam($page.url.search, 'tag', tag.identifier)}`}
				class={`flex gap-2 my-1 p-1 hover:bg-primary-500 items-center rounded ${active ? 'text-primary-500' : ''}`}
				on:click={() => (open = false)}
			>
				<TagIcon size={22} class="shrink-0" />
				<span class="text-base">{tag.displayName}</span>
			</DropdownItem>
		{/if}
	{/each}
	{#each $state.devices as device}
		{@const active =
			$globalNavSelectedTargetType === 'device' &&
			$globalNavSelectedDevice?.identifier === device.identifier}
		{#if isSearched(search, device.displayName)}
			<DropdownItem
				href={`?${buildGlobalNavSearchParam($page.url.search, 'device', device.identifier)}`}
				class={`flex gap-2 my-1 p-1 hover:bg-primary-500 items-center rounded ${active ? 'text-primary-500' : ''}`}
				on:click={() => (open = false)}
			>
				<HardDrive size={22} class="shrink-0" />
				<span class="text-base">{device.displayName}</span>
			</DropdownItem>
		{/if}
	{/each}
</Dropdown>
