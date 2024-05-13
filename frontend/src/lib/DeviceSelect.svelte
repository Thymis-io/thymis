<script lang="ts">
	import { t } from 'svelte-i18n';
	import { queryParam } from 'sveltekit-search-params';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import { Button, Dropdown, DropdownItem, Search } from 'flowbite-svelte';
	import { ChevronDownSolid } from 'flowbite-svelte-icons';
	import { page } from '$app/stores';
	import type { State } from './state';
	export let state: State;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = state.tags.find((t) => t.identifier === $tagParam);
	$: device = state.devices.find((d) => d.identifier === $deviceParam);

	let search = '';

	const otherUrlParams = () => {
		const params = new URLSearchParams($page.url.search);
		params.delete('tag');
		params.delete('device');
		return params.toString();
	};

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
		{#if tag}
			<TagIcon size={20} /> {tag.displayName}
		{:else if device}
			<HardDrive size={20} /> {device.displayName}
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
	{#each state.tags as tag}
		{#if isSearched(search, tag.displayName)}
			<DropdownItem
				href={`?tag=${tag.identifier}&${otherUrlParams()}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<TagIcon />
				{tag.displayName}
			</DropdownItem>
		{/if}
	{/each}
	{#each state.devices as device}
		{#if isSearched(search, device.displayName)}
			<DropdownItem
				href={`?device=${device.identifier}&${otherUrlParams()}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<HardDrive />
				{device.displayName}
			</DropdownItem>
		{/if}
	{/each}
</Dropdown>
