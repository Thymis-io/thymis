<script lang="ts">
	import { t } from 'svelte-i18n';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import { Button, Dropdown, DropdownItem, Search } from 'flowbite-svelte';
	import ChevronDownOutline from 'flowbite-svelte-icons/ChevronDownOutline.svelte';
	import { page } from '$app/stores';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '../state';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

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

<Button class="text-base w-full flex gap-2 justify-start p-2" color="alternative">
	{#if $globalNavSelectedTag}
		<TagIcon size={'1rem'} class="min-w-4 text-primary-600 dark:text-primary-400" />
		<span
			class="font-semibold text-primary-600 dark:text-primary-400 truncate"
			title={$globalNavSelectedTag?.displayName}
		>
			{$globalNavSelectedTag?.displayName}
		</span>
	{:else if $globalNavSelectedConfig}
		<HardDrive size={'1rem'} class="min-w-4 text-primary-600 dark:text-primary-400" />
		<span
			class="font-semibold text-primary-600 dark:text-primary-400 truncate"
			title={$globalNavSelectedConfig?.displayName}
		>
			{$globalNavSelectedConfig?.displayName}
		</span>
	{:else}
		<span class="font-semibold truncate" title={$t('common.no-tag-or-device-selected')}>
			{$t('common.no-tag-or-device-selected')}
		</span>
	{/if}
	<ChevronDownOutline class="h-4 text-white ml-auto dark:text-white" />
</Button>
<Dropdown
	class="overflow-y-auto px-3 h-60 text-sm relative"
	containerClass="z-50 left-4 right-4 flex flex-col whitespace-nowrap"
	strategy="absolute"
	bind:open
>
	<div slot="header" class="p-3 pb-0">
		<Search size="sm" bind:value={search} placeholder={$t('common.search')} />
	</div>
	{#each $state.tags as tag}
		{@const active =
			$globalNavSelectedTargetType === 'tag' &&
			$globalNavSelectedTag?.identifier === tag.identifier}
		{@const subpage = [
			'/configuration/edit',
			targetShouldShowVNC(tag, $state) ? '/configuration/vnc' : undefined
		].includes($page.url.pathname)
			? $page.url.pathname
			: '/configuration/edit'}
		{#if isSearched(search, tag.displayName)}
			<DropdownItem
				href={`${subpage}?${buildGlobalNavSearchParam($page.url.search, 'tag', tag.identifier)}`}
				class={`flex gap-2 my-1 p-1 hover:bg-primary-500 items-center rounded ${active ? 'text-primary-600 dark:text-primary-400' : ''}`}
				on:click={() => (open = false)}
			>
				<TagIcon size={'1rem'} class="min-w-4" />
				<span class="text-base truncate" title={tag.displayName}>{tag.displayName}</span>
			</DropdownItem>
		{/if}
	{/each}
	{#each $state.devices as device}
		{@const active =
			$globalNavSelectedTargetType === 'config' &&
			$globalNavSelectedConfig?.identifier === device.identifier}
		{@const subpage = [
			'/configuration/configuration-details',
			'/configuration/edit',
			targetShouldShowVNC(device, $state) ? '/configuration/vnc' : undefined,
			'/configuration/terminal'
		].includes($page.url.pathname)
			? $page.url.pathname
			: '/configuration/configuration-details'}
		{#if isSearched(search, device.displayName)}
			<DropdownItem
				href={`${subpage}?${buildGlobalNavSearchParam($page.url.search, 'config', device.identifier)}`}
				class={`flex gap-2 my-1 p-1 hover:bg-primary-500 items-center rounded ${active ? 'text-primary-600 dark:text-primary-400' : ''}`}
				on:click={() => (open = false)}
			>
				<HardDrive size={'1rem'} class="min-w-4" />
				<span class="text-base truncate" title={device.displayName}>{device.displayName}</span>
			</DropdownItem>
		{/if}
	{/each}
</Dropdown>
