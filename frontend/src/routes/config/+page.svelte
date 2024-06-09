<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card, Toggle, Listgroup, ListgroupItem, Tooltip, P, Button } from 'flowbite-svelte';
	import ModuleList from '$lib/config/ModuleList.svelte';
	import { saveState } from '$lib/state';
	import type { ModuleSettings, Tag, Device, Module } from '$lib/state';
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

	$: modules = getModules($selectedTag, $selectedDevice);

	const getOrigin = (target: Tag | Device | undefined) => {
		return target?.displayName;
	};

	const getModuleSettings = (tag: Tag | undefined, device: Device | undefined) => {
		if (tag) {
			return tag.modules.map((m) => ({ origin: getOrigin(tag), ...m }));
		}

		if (device) {
			let usedTags = device.tags.flatMap(
				(t) => data.state.tags.find((tag) => tag.identifier === t) ?? []
			);
			return [
				...device.modules.map((m) => ({ origin: getOrigin(device), ...m })),
				...usedTags.flatMap((t) =>
					t.modules.map((m) => ({ origin: getOrigin(t), priority: t.priority, ...m }))
				)
			];
		}
	};

	const getSelfModuleSettings = (target: Tag | Device | undefined) => {
		return target?.modules.map((m) => ({ origin: getOrigin(target), ...m })) ?? [];
	};

	const getSelfModules = (selectedTarget: Tag | Device | undefined) => {
		let settings = getSelfModuleSettings(selectedTarget);
		return data.availableModules.filter((m) => settings.find((s) => s.type === m.type)) ?? [];
	};

	const getOtherSettings = (target: Device | Tag | undefined, module: Module | undefined) => {
		if (!target) {
			return [];
		}

		let settings = getModuleSettings(
			!('tags' in target) ? (target as Tag) : undefined,
			'tags' in target ? (target as Device) : undefined
		);

		return settings?.filter((s) => s.type === module?.type);
	};

	const getModules = (tag: Tag | undefined, device: Device | undefined) => {
		let settings = getModuleSettings(tag, device);
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
		tag: Tag | undefined,
		device: Device | undefined
	) => {
		let settings = getModuleSettings(tag, device);
		return settings?.filter(
			(s) => s.type === module.type && Object.keys(s.settings).includes(settingKey)
		);
	};

	const getSetting = (
		module: ModuleSettings | Module,
		settingKey: string,
		tag: Tag | undefined,
		device: Device | undefined
	) => {
		let settings = getSettings(module, settingKey, tag, device);

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
		console.log(target, targetModule);

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
<div class="flex gap-10 mb-4">
	{#if modules.find((m) => m.type === $selectedConfigModule?.type)}
		<Button
			on:click={() => {
				if ($selectedConfigModule) removeModule($selectedConfigTarget, $selectedConfigModule);
			}}
		>
			{$t('config.uninstall')}
		</Button>
	{:else}
		<Button
			on:click={() => {
				if ($selectedConfigModule) addModule($selectedConfigTarget, $selectedConfigModule);
			}}
		>
			{$t('config.install')}
		</Button>
	{/if}
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
	{#if $selectedConfigModule}
		<div class="col-span-4">
			<ConfigModuleCard
				module={$selectedConfigModule}
				settings={getSelfModuleSettings($selectedConfigTarget).find(
					(s) => s.type === $selectedConfigModule?.type
				)}
				otherSettings={getOtherSettings($selectedTarget, $selectedConfigModule)}
				setSetting={(module, key, value) => setSetting($selectedConfigTarget, module, key, value)}
			/>
		</div>
	{/if}
</div>
