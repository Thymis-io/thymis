<script lang="ts">
	import { queryParam } from 'sveltekit-search-params';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import { Button, Dropdown, Search } from 'flowbite-svelte';
	import { ChevronDownSolid } from 'flowbite-svelte-icons';
	import type { PageData } from '../routes/$types';
	import { page } from '$app/stores';

	export let data: PageData;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = data.state.tags.find((t) => t.name === $tagParam);
	$: device = data.state.devices.find((d) => d.hostname === $deviceParam);

	const otherUrlParams = () => {
		const params = new URLSearchParams($page.url.search);
		params.delete('tag');
		params.delete('device');
		return params.toString();
	};
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
			<a
				href={`?tag=${tag.name}&${otherUrlParams()}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<TagIcon />
				{tag.name}
			</a>
		{/each}
		{#each data.state.devices as device}
			<a
				href={`?device=${device.hostname}&${otherUrlParams()}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<HardDrive />
				{device.displayName}
			</a>
		{/each}
	</div>
</Dropdown>
