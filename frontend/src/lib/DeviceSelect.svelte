<script lang="ts">
	import { queryParam } from 'sveltekit-search-params';
	import { ListBox, ListBoxItem, popup } from '@skeletonlabs/skeleton';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { state } from './state';

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = $state?.tags.find((t) => t.name === $tagParam);
	$: device = $state?.devices.find((d) => d.hostname === $deviceParam);
</script>

<button
	class="btn variant-filled w-full justify-between"
	use:popup={{
		event: 'click',
		target: 'selectCombobox',
		placement: 'bottom'
	}}
>
	<div class="flex gap-2">
		{#if tag}
			<TagIcon /> {tag.name}
		{:else if device}
			<HardDrive /> {device.displayName}
		{/if}
	</div>
	<span><ChevronDown /></span>
</button>
<div class="card w-80 shadow-xl py-2 z-50" data-popup="selectCombobox">
	<ListBox rounded="rounded-none">
		{#each $state?.tags ?? [] as tag}
			<!-- <a href="/config?tag={tag.name}"> -->
			<a
				href="#"
				on:click={() => {
					$tagParam = tag.name;
					$deviceParam = null;
				}}
			>
				<ListBoxItem
					group={''}
					value={tag.name}
					name={tag.name}
					hover={'hover:variant-filled'}
					active={''}
					class="flex"
				>
					<svelte:fragment slot="lead"><TagIcon /></svelte:fragment>
					{tag.name}
				</ListBoxItem>
			</a>
		{/each}
		{#each $state?.devices ?? [] as device}
			<!-- <a href="/config?device={device.hostname}"> -->
			<a
				href="#"
				on:click={() => {
					$deviceParam = device.hostname;
					$tagParam = null;
				}}
			>
				<ListBoxItem
					group={''}
					value={device.hostname}
					name={device.hostname}
					hover={'hover:variant-filled'}
					active={''}
					class="flex"
				>
					<svelte:fragment slot="lead"><HardDrive /></svelte:fragment>
					{device.displayName}
				</ListBoxItem>
			</a>
		{/each}
	</ListBox>
</div>
