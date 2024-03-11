<script lang="ts">
	import { queryParam } from 'sveltekit-search-params';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import { Button, Dropdown, Search } from 'flowbite-svelte';
	import { ChevronDownSolid } from 'flowbite-svelte-icons';
	import { page } from '$app/stores';
	import type { State } from './state';
	export let state: State;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = state.tags.find((t) => t.name === $tagParam);
	$: device = state.devices.find((d) => d.hostname === $deviceParam);

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
		{:else}
			No tag or device selected
		{/if}
	</div>
	<ChevronDownSolid class="h-4 ms-2 text-white dark:text-white" /></Button
>
<Dropdown class="overflow-y-auto px-3 pb-3 text-sm h-44">
	<div slot="header" class="p-3">
		<Search size="md" />
		{#each state.tags as tag}
			<a
				href={`?tag=${tag.name}&${otherUrlParams()}`}
				class={'flex gap-2 my-1 p-1 hover:bg-primary-500'}
			>
				<TagIcon />
				{tag.name}
			</a>
		{/each}
		{#each state.devices as device}
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
