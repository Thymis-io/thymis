<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Config, type Module } from '$lib/state';
	import {
		buildGlobalNavSearchParam,
		buildConfigSelectModuleSearchParam
	} from '$lib/searchParamHelpers';
	import { page } from '$app/stores';
	import { Button } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import TagIcon from 'lucide-svelte/icons/tag';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import ModuleIcon from '$lib/config/ModuleIcon.svelte';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		config: Config;
		availableModules: Module[];
		class?: string;
	}

	let { globalState, config, availableModules, class: className = '' }: Props = $props();

	let currentlyEditingConfig: Config | undefined = $state(undefined);

	const getOwnModules = (config: Config, availableModules: Module[]) => {
		return config.modules
			.map((module) => availableModules.find((m) => m.type === module.type))
			.filter((m) => !!m);
	};

	const findTag = (identifier: string) => {
		return globalState.tags.find((t) => t.identifier === identifier);
	};
</script>

<EditTagModal {globalState} bind:currentlyEditingConfig />
<Section class={className} title={$t('configuration-details.config')}>
	<p class="text-base">{$t('configuration-details.modules')}</p>
	<div class="flex gap-2 items-center flex-wrap">
		{#each getOwnModules(config, availableModules) as module}
			<a
				href={`/configuration/edit?${buildConfigSelectModuleSearchParam(
					globalState,
					$page.url.search,
					'config',
					config.identifier,
					'config',
					config.identifier,
					module
				)}`}
			>
				<Button pill size="sm" class="flex p-2 py-1 gap-2 text-nowrap text-base items-center">
					<ModuleIcon {module} theme="dark" />
					{module.displayName}
					<Pen size="16" />
				</Button>
			</a>
		{/each}
	</div>
	<p class="text-base">{$t('configuration-details.tags')}</p>
	<div class="flex gap-2 items-center">
		<div class="flex gap-2 flex-wrap">
			{#each config.tags as tag, i}
				<Button
					pill
					size="sm"
					class="flex p-2 py-1 gap-2 text-nowrap text-base items-center"
					href={`/configuration/edit?${buildGlobalNavSearchParam(globalState, $page.url.search, 'tag', tag)}`}
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
			on:click={() => (currentlyEditingConfig = config)}
		>
			<Pen size="16" />
			<span class="text-sm">{$t('configuration-details.edit-tags')}</span>
		</Button>
	</div>
</Section>
