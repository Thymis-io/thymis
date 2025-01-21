<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card } from 'flowbite-svelte';
	import ModuleList from '$lib/config/ModuleList.svelte';
	import {
		getDeviceByIdentifier,
		getTagByIdentifier,
		globalNavSelectedTargetType,
		saveState
	} from '$lib/state';
	import {
		type ModuleSettings,
		type ModuleSettingsWithOrigin,
		type Tag,
		type Device,
		type Module,
		type Origin,
		globalNavSelectedTarget,
		state,
		globalNavSelectedTag,
		globalNavSelectedConfig
	} from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import type { PageData } from '../../$types';
	import ConfigModuleCard from '$lib/config/ModuleCard.svelte';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import TagIcon from 'lucide-svelte/icons/tag';
	import { queryParam } from 'sveltekit-search-params';
	import { derived } from 'svelte/store';
	import { page } from '$app/stores';
	import Tabbar from '$lib/components/Tabbar.svelte';

	export let data: PageData;

	const configSelectedModule = derived(
		[page, queryParam('config-selected-module')],
		([$page, m]) => {
			let availableModules = $page.data.availableModules as Module[];
			return availableModules.find((module) => module.type === m);
		}
	);
	const configSelectedModuleContextType = queryParam('config-selected-module-context-type');
	const configSelectedModuleContext = derived(
		[
			configSelectedModuleContextType,
			queryParam('config-selected-module-context-identifier'),
			state
		],
		([$contextType, $contextIdentifier, s]) => {
			if ($contextType === 'tag') {
				return getTagByIdentifier(s, $contextIdentifier);
			} else if ($contextType === 'config') {
				return getDeviceByIdentifier(s, $contextIdentifier);
			}
		}
	);

	const getOrigin = (target: Tag | Device): Origin => {
		return {
			originId: target.identifier,
			originContext: 'tags' in target ? 'config' : 'tag',
			originName: target.displayName
		};
	};

	const getModuleSettings = (target: Tag | Device | undefined): ModuleSettingsWithOrigin[] => {
		if (!target) {
			return [];
		}

		let ownModules: ModuleSettingsWithOrigin[] = getOwnModuleSettings(target);
		let tagModules: ModuleSettingsWithOrigin[] = [];

		if ('tags' in target) {
			let usedTags = target.tags.flatMap((t) => getTagByIdentifier($state, t) ?? []);

			tagModules = usedTags.flatMap((t) =>
				t.modules.map((m) => ({ ...getOrigin(t), priority: t.priority, ...m }))
			);
		}

		return [...ownModules, ...tagModules];
	};

	const getOwnModuleSettings = (target: Tag | Device | undefined): ModuleSettingsWithOrigin[] => {
		return target?.modules.map((m) => ({ ...getOrigin(target), priority: undefined, ...m })) ?? [];
	};

	const getSelfModules = (selectedTarget: Tag | Device | undefined) => {
		let settings = getOwnModuleSettings(selectedTarget);
		return data.availableModules.filter((m) => settings.find((s) => s.type === m.type)) ?? [];
	};

	const getOtherSettings = (target: Device | Tag | undefined, module: Module | undefined) => {
		return getModuleSettings(target)?.filter((s) => s.type === module?.type);
	};

	const removeModule = (target: Tag | Device | undefined, module: ModuleSettings | Module) => {
		if (target) {
			target.modules = target.modules.filter((m) => m.type !== module.type);
		}
		saveState();
	};

	const getSettings = (
		module: ModuleSettings | Module,
		settingKey: string,
		target: Tag | Device | undefined
	) => {
		let settings = getModuleSettings(target);
		return settings?.filter(
			(s) => s.type === module.type && Object.keys(s.settings).includes(settingKey)
		);
	};

	const getSetting = (
		module: ModuleSettings | Module,
		settingKey: string,
		target: Tag | Device | undefined
	) => {
		let settings = getSettings(module, settingKey, target);

		if (settings && settings.length >= 1) {
			return settings[0].settings[settingKey];
		}
	};

	const setSetting = (
		target: Tag | Device | undefined,
		module: ModuleSettings | Module,
		settingKey: string,
		value: any
	) => {
		let targetModule = target?.modules.find((m) => m.type === module.type);

		if (target && targetModule) {
			if (value !== undefined && value !== null) {
				targetModule.settings[settingKey] = value;
			} else {
				delete targetModule.settings[settingKey];
			}
		}

		saveState();
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
			configSelectedModuleContext={$configSelectedModuleContext}
			configSelectedModuleContextType={$configSelectedModuleContextType}
			{removeModule}
		>
			<slot slot="icon">
				{#if $globalNavSelectedTag}
					<TagIcon size="20" />
				{:else if $globalNavSelectedConfig}
					<HardDrive size="20" />
				{/if}
			</slot>
		</ModuleList>
		{#each $globalNavSelectedConfig?.tags ?? [] as tagIdentifier}
			{@const usedTag = getTagByIdentifier($state, tagIdentifier)}
			<div class="mt-6">
				<ModuleList
					contextType="tag"
					context={usedTag}
					selfModules={getSelfModules(usedTag)}
					configSelectedModule={$configSelectedModule}
					configSelectedModuleContext={$configSelectedModuleContext}
					configSelectedModuleContextType={$configSelectedModuleContextType}
				>
					<TagIcon slot="icon" size="20" />
				</ModuleList>
			</div>
		{/each}
	</Card>
	{#if $configSelectedModule && $configSelectedModuleContext?.modules.find((m) => m.type === $configSelectedModule.type)}
		<ConfigModuleCard
			module={$configSelectedModule}
			settings={getOwnModuleSettings($configSelectedModuleContext).find(
				(s) => s.type === $configSelectedModule?.type
			)}
			otherSettings={getOtherSettings($globalNavSelectedTarget, $configSelectedModule)}
			setSetting={(module, key, value) =>
				setSetting($configSelectedModuleContext, module, key, value)}
			showRouting={$globalNavSelectedTargetType === 'config'}
			canEdit={$globalNavSelectedTarget === $configSelectedModuleContext}
		/>
	{/if}
</div>
