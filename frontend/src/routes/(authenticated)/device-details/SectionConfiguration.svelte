<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Device, type Module, state } from '$lib/state';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { page } from '$app/stores';
	import { Button } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import TagIcon from 'lucide-svelte/icons/tag';
	import EditTagModal from '../devices/EditTagModal.svelte';

	export let device: Device;
	export let availableModules: Module[];

	let currentlyEditingDevice: Device | undefined = undefined;

	const getOwnModules = (device: Device, availableModules: Module[]) => {
		return device.modules
			.map((module) => availableModules.find((m) => m.type === module.type))
			.filter((m) => !!m);
	};

	const findTag = (identifier: string) => {
		return $state.tags.find((t) => t.identifier === identifier);
	};

	let className = '';
	export { className as class };
</script>

<EditTagModal bind:currentlyEditingDevice />
<Section class={className} title={$t('device-details.config')}>
	<p>{$t('device-details.modules')}:</p>
	<div class="flex gap-2 items-center flex-wrap">
		{#each getOwnModules(device, availableModules) as module}
			<Button pill size="sm" class="p-2 py-1 gap-2 text-nowrap">
				<img src={module.icon ?? '/favicon.png'} alt={module.displayName} class="w-5 h-5" />
				{module.displayName}
			</Button>
		{/each}
		<a href={`/config?${buildGlobalNavSearchParam($page.url.search, 'device', device.identifier)}`}>
			<button class="btn ml-4 p-0">
				<Pen size="20" />
			</button>
		</a>
	</div>
	<p>{$t('device-details.tags')}:</p>
	<div class="flex gap-2 items-center">
		<div class="flex gap-2 flex-wrap">
			{#each device.tags as tag, i}
				<Button
					pill
					size="sm"
					class="p-2 py-1"
					href={`/config?${buildGlobalNavSearchParam($page.url.search, 'tag', tag)}`}
				>
					<TagIcon size={15} class="mr-1" />
					<span class="text-nowrap">
						{findTag(tag)?.displayName ?? tag}
					</span>
				</Button>
			{/each}
		</div>
		<button class="btn ml-4 p-0" on:click={() => (currentlyEditingDevice = device)}>
			<Pen size="20" />
		</button>
	</div>
</Section>
