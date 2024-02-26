<script lang="ts">
	import { queryParam } from 'sveltekit-search-params';
	import { ListBox, ListBoxItem, popup } from '@skeletonlabs/skeleton';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import type { State } from './state';
	import { Button, Dropdown, Search } from 'flowbite-svelte';
	import { ChevronDownSolid } from 'flowbite-svelte-icons';
	import type { PageData } from '../routes/$types';

	export let data: PageData;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = data.state.tags.find((t) => t.name === $tagParam);
	$: device = data.state.devices.find((d) => d.hostname === $deviceParam);
</script>

<Button class="w-full flex justify-between">
	<div class="flex gap-2">
		{#if tag}
			<TagIcon size={20} /> {tag.name}
		{:else if device}
			<HardDrive size={20} /> {device.displayName}
		{/if}
	</div>
	<ChevronDownSolid class="h-4 ms-2 text-white dark:text-white" /></Button
>
<Dropdown class="overflow-y-auto px-3 pb-3 text-sm h-44">
	<div slot="header" class="p-3">
		<Search size="md" />
		{#each data.state.tags as tag}
			<!-- <a href="/config?tag={tag.name}"> -->
			<a
				href="#"
				on:click={() => {
					$tagParam = tag.name;
					$deviceParam = null;
				}}
			>
				<div class={'flex gap-2 my-1 py-1 hover:bg-primary-500'}>
					<TagIcon />
					{tag.name}
				</div>
			</a>
		{/each}
		{#each data.state.devices as device}
			<!-- <a href="/config?device={device.hostname}"> -->
			<a
				href="#"
				on:click={() => {
					$deviceParam = device.hostname;
					$tagParam = null;
				}}
			>
				<div class={'flex gap-2 my-1 py-1 hover:bg-primary-500'}>
					<HardDrive />
					{device.displayName}
				</div>
			</a>
		{/each}
	</div>
</Dropdown>
