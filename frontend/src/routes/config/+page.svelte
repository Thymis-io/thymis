<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card, Toggle, Listgroup, ListgroupItem, Tooltip, P, Button } from 'flowbite-svelte';
	import ModuleList from '$lib/config/ModuleList.svelte';
	import { saveState } from '$lib/state';
	import type {
		ModuleSettings,
		ModuleSettingsWithOrigin,
		Tag,
		Device,
		Module,
		Origin
	} from '$lib/state';
	import {
		selectedDevice,
		selectedTag,
		selectedTarget,
		selectedContext,
		selectedConfigTarget,
		selectedConfigModule
	} from '$lib/deviceSelectHelper';
	import DeployActions from '$lib/DeployActions.svelte';
	import type { PageData } from './$types';
	import ConfigModuleCard from '$lib/config/ConfigModuleCard.svelte';
	import { HardDrive, TagIcon } from 'lucide-svelte';

	export let data: PageData;

	$: modules = getModules($selectedTarget);

	const getOrigin = (target: Tag | Device): Origin => {
		return {
			originId: target.identifier,
			originContext: 'tags' in target ? 'device' : 'tag',
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
			let usedTags = target.tags.flatMap(
				(t) => data.state.tags.find((tag) => tag.identifier === t) ?? []
			);

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

	const getModules = (target: Tag | Device | undefined) => {
		let settings = getModuleSettings(target);
		return data.availableModules.filter((m) => settings?.find((s) => s.type === m.type)) ?? [];
	};

	const addModule = (target: Tag | Device | undefined, module: ModuleSettings | Module) => {
		if (target && !target.modules.find((m) => m.type === module.type)) {
			target.modules = [...target.modules, { type: module.type, settings: {} }];
		}

		saveState(data.state);
	};

	const removeModule = (target: Tag | Device | undefined, module: ModuleSettings | Module) => {
		if (target) {
			target.modules = target.modules.filter((m) => m.type !== module.type);
		}

		saveState(data.state);
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
		addModule(target, module);

		let targetModule = target?.modules.find((m) => m.type === module.type);

		if (targetModule) {
			if (value !== undefined && value !== null) {
				targetModule.settings[settingKey] = value;
			} else {
				delete targetModule.settings[settingKey];
			}
		}

		saveState(data.state);
	};
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">
		{#if $selectedTag}
			{$t('config.header.tag-module', {
				values: { module: $selectedConfigModule?.displayName, tag: $selectedTag.displayName }
			})}
		{:else if $selectedDevice}
			{$t('config.header.device-module', {
				values: { module: $selectedConfigModule?.displayName, device: $selectedDevice.displayName }
			})}
		{:else}
			{$t('config.header.module', { values: { module: $selectedConfigModule?.displayName } })}
		{/if}
	</h1>
	<DeployActions />
</div>
<div class="grid grid-flow-row grid-cols-5 gap-4">
	<Card class="col-span-1 max-w-none">
		<ModuleList
			target={$selectedTarget}
			selfModules={getSelfModules($selectedTarget)}
			context={$selectedContext}
		>
			<slot slot="icon">
				{#if $selectedTag}
					<TagIcon />
				{:else if $selectedDevice}
					<HardDrive />
				{/if}
			</slot>
		</ModuleList>
		{#each $selectedDevice?.tags ?? [] as tagIdentifier}
			{@const usedTag = data.state.tags.find((t) => t.identifier === tagIdentifier)}
			<ModuleList target={usedTag} selfModules={getSelfModules(usedTag)} context="tag">
				<TagIcon slot="icon" />
			</ModuleList>
		{/each}
	</Card>
	{#if $selectedConfigModule && $selectedConfigTarget?.modules.find((m) => m.type === $selectedConfigModule.type)}
		<div class="col-span-4">
			<ConfigModuleCard
				module={$selectedConfigModule}
				settings={getOwnModuleSettings($selectedConfigTarget).find(
					(s) => s.type === $selectedConfigModule?.type
				)}
				otherSettings={getOtherSettings($selectedTarget, $selectedConfigModule)}
				setSetting={(module, key, value) => setSetting($selectedConfigTarget, module, key, value)}
				showRouting={$selectedContext === 'device'}
				canEdit={$selectedTarget === $selectedConfigTarget}
			/>
		</div>
	{/if}
</div>
