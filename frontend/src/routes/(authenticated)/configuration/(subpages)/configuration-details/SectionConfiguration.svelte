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
	import EditTagModal from '$lib/EditTagModal.svelte';

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
<Section class={className} title={$t('configuration-details.config')}>
	<p class="text-base">{$t('configuration-details.modules')}</p>
	<div class="flex gap-2 items-center flex-wrap">
		{#each getOwnModules(device, availableModules) as module}
			<a
				href={`/configuration/edit?${buildConfigSelectModuleSearchParam(
					$page.url.search,
					'config',
					device.identifier,
					'config',
					device.identifier,
					module
				)}`}
			>
				<Button pill size="sm" class="p-2 py-1 gap-2 text-nowrap">
					<img src={module.icon ?? '/favicon.png'} alt={module.displayName} class="w-4 h-4" />
					{module.displayName}
					<Pen size="16" />
				</Button>
			</a>
		{/each}
	</div>
	<p class="text-base">{$t('configuration-details.tags')}</p>
	<div class="flex gap-2 items-center">
		<div class="flex gap-2 flex-wrap">
			{#each device.tags as tag, i}
				<Button
					pill
					size="sm"
					class="p-2 py-1 gap-2"
					href={`/configuration/edit?${buildGlobalNavSearchParam($page.url.search, 'tag', tag)}`}
				>
					<TagIcon size="16" />
					<span class="text-nowrap">
						{findTag(tag)?.displayName ?? tag}
					</span>
					<Pen size="16" />
				</Button>
			{/each}
		</div>
		<Button
			color="alternative"
			class="p-2 py-1.5 gap-2"
			on:click={() => (currentlyEditingDevice = device)}
		>
			<Pen size="16" />
			<span class="text-sm">{$t('configuration-details.edit-tags')}</span>
		</Button>
	</div>
</Section>
