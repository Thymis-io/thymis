<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card } from 'flowbite-svelte';
	import ModuleList from '$lib/config/ModuleList.svelte';
	import {
		getTagByIdentifier,
		globalNavSelectedTargetType,
		saveState,
		globalNavSelectedTarget,
		globalState,
		globalNavSelectedTag,
		globalNavSelectedConfig
	} from '$lib/state';
	import type {
		ModuleSettings,
		ModuleSettingsWithOrigin,
		Tag,
		Config,
		Module,
		Origin
	} from '$lib/state';
	import {
		configSelectedModuleContext,
		configSelectedModuleContextType
	} from '$lib/searchParamHelpers';
	import type { PageData } from './$types';
	import ModuleCard from '$lib/config/ModuleCard.svelte';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import TagIcon from 'lucide-svelte/icons/tag';
	import { queryParam } from 'sveltekit-search-params';
	import { derived } from 'svelte/store';
	import { page } from '$app/stores';

	export let data: PageData;

	const configSelectedModule = derived(
		[page, queryParam('config-selected-module')],
		([$page, m]) => {
			let availableModules = $page.data.availableModules as Module[];
			return availableModules.find((module) => module.type === m);
		}
	);

	const getOrigin = (target: Tag | Config): Origin => {
		return {
			originId: target.identifier,
			originContext: 'tags' in target ? 'config' : 'tag',
			originName: target.displayName
		};
	};

	const getModuleSettings = (target: Tag | Config | undefined): ModuleSettingsWithOrigin[] => {
		if (!target) {
			return [];
		}

		let ownModules: ModuleSettingsWithOrigin[] = getOwnModuleSettings(target);
		let tagModules: ModuleSettingsWithOrigin[] = [];

		if ('tags' in target) {
			let usedTags = target.tags.flatMap((t) => getTagByIdentifier($globalState, t) ?? []);

			tagModules = usedTags.flatMap((t) =>
				t.modules.map((m) => ({ ...getOrigin(t), priority: t.priority, ...m }))
			);
		}

		return [...ownModules, ...tagModules];
	};

	const getOwnModuleSettings = (target: Tag | Config | undefined): ModuleSettingsWithOrigin[] => {
		return target?.modules.map((m) => ({ ...getOrigin(target), priority: undefined, ...m })) ?? [];
	};

	const getSelfModules = (selectedTarget: Tag | Config | undefined) => {
		let settings = getOwnModuleSettings(selectedTarget);
		return data.availableModules.filter((m) => settings.find((s) => s.type === m.type)) ?? [];
	};

	const getOtherSettings = (target: Config | Tag | undefined, module: Module | undefined) => {
		return getModuleSettings(target)?.filter((s) => s.type === module?.type);
	};
</script>

<div class="grid grid-flow-row grid-cols-1 md:grid-cols-[250px_auto] gap-4">
	<Card class="max-w-none" padding={'sm'}>
		<ModuleList
			contextType={$globalNavSelectedTargetType}
			context={$globalNavSelectedTarget}
			selfModules={getSelfModules($globalNavSelectedTarget)}
			availableModules={data.availableModules}
			configSelectedModule={$configSelectedModule}
		>
			<slot slot="icon">
				{#if $globalNavSelectedTag}
					<TagIcon size="20" />
				{:else if $globalNavSelectedConfig}
					<FileCode size="20" />
				{/if}
			</slot>
		</ModuleList>
		{#each $globalNavSelectedConfig?.tags ?? [] as tagIdentifier}
			{@const usedTag = getTagByIdentifier($globalState, tagIdentifier)}
			<div class="mt-6">
				<ModuleList
					contextType="tag"
					context={usedTag}
					selfModules={getSelfModules(usedTag)}
					configSelectedModule={$configSelectedModule}
				>
					<TagIcon slot="icon" size="20" />
				</ModuleList>
			</div>
		{/each}
	</Card>
	{#if $configSelectedModule && $configSelectedModuleContext?.modules.find((m) => m.type === $configSelectedModule.type)}
		<ModuleCard
			module={$configSelectedModule}
			configSelectedModuleContextType={$configSelectedModuleContextType}
			settings={getOwnModuleSettings($configSelectedModuleContext).find(
				(s) => s.type === $configSelectedModule?.type
			)}
			otherSettings={getOtherSettings($globalNavSelectedTarget, $configSelectedModule)}
			showRouting={$globalNavSelectedTargetType === 'config'}
			canEdit={$globalNavSelectedTarget === $configSelectedModuleContext}
		/>
	{/if}
</div>
