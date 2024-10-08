<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Device, type Module, state } from '$lib/state';
	import {
		buildGlobalNavSearchParam,
		buildConfigSelectModuleSearchParam
	} from '$lib/searchParamHelpers';
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
	<p>{$t('device-details.modules')}</p>
	<div class="flex gap-2 items-center flex-wrap">
		{#each getOwnModules(device, availableModules) as module}
			<a
				href={`/config?${buildConfigSelectModuleSearchParam(
					$page.url.search,
					'device',
					device.identifier,
					'device',
					device.identifier,
					module
				)}`}
			>
				<Button pill size="sm" class="p-4 py-2 gap-2 text-nowrap">
					<img src={module.icon ?? '/favicon.png'} alt={module.displayName} class="w-5 h-5" />
					{module.displayName}
					<Pen size="20" />
				</Button>
			</a>
		{/each}
	</div>
	<p>{$t('device-details.tags')}</p>
	<div class="flex gap-2 items-center">
		<div class="flex gap-2 flex-wrap">
			{#each device.tags as tag, i}
				<Button
					pill
					size="sm"
					class="p-4 py-2 gap-2"
					href={`/config?${buildGlobalNavSearchParam($page.url.search, 'tag', tag)}`}
				>
					<TagIcon size={20} />
					<span class="text-nowrap">
						{findTag(tag)?.displayName ?? tag}
					</span>
					<Pen size="20" />
				</Button>
			{/each}
		</div>
		<Button color="alternative" class="gap-2" on:click={() => (currentlyEditingDevice = device)}>
			<Pen size="20" />
			<span>{$t('device-details.edit-tags')}</span>
		</Button>
	</div>
</Section>
