<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card, Toggle, Listgroup, ListgroupItem, Tooltip, P, Button } from 'flowbite-svelte';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import ConfigTextarea from '$lib/config/ConfigTextarea.svelte';
	import ConfigSelectOne from '$lib/config/ConfigSelectOne.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import { saveState } from '$lib/state';
	import type { ModuleSettings, Tag, Device, Module } from '$lib/state';

	import Info from 'lucide-svelte/icons/info';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import DeployActions from '$lib/DeployActions.svelte';
	import type { PageData } from './$types';
	import { page } from '$app/stores';

	export let data: PageData;

	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');
	const moduleParam = queryParam('module');

	$: tag = data.state.tags.find((t) => t.identifier === $tagParam);
	$: device = data.state.devices.find((d) => d.identifier === $deviceParam);
	$: modules = getModules(tag, device);
	$: selectedModule = data.availableModules.find((m) => m.type === $moduleParam);

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
				...usedTags.flatMap((t) => t.modules.map((m) => ({ origin: getOrigin(t), ...m })))
			];
		}
	};

	const getModules = (tag: Tag | undefined, device: Device | undefined) => {
		let settings = getModuleSettings(tag, device);
		return data.availableModules.filter((m) => settings?.find((s) => s.type === m.type)) ?? [];
	};

	const addModule = (module: ModuleSettings | Module) => {
		if (tag && !tag.modules.find((m) => m.type === module.type)) {
			tag.modules = [...tag.modules, { type: module.type, settings: {} }];
		}

		if (device && !device.modules.find((m) => m.type === module.type)) {
			device.modules = [...device.modules, { type: module.type, settings: {} }];
		}

		saveState(data.state);
	};

	const removeModule = (module: ModuleSettings | Module) => {
		if (tag) {
			tag.modules = tag.modules.filter((m) => m.type !== module.type);
		}

		if (device) {
			device.modules = device.modules.filter((m) => m.type !== module.type);
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

	const setSetting = (module: ModuleSettings | Module, settingKey: string, value: any) => {
		addModule(module);

		let tagModule = tag?.modules.find((m) => m.type === module.type);

		if (tag && tagModule) {
			if (value !== undefined && value !== null) {
				tagModule.settings[settingKey] = value;
			} else {
				delete tagModule.settings[settingKey];
			}
		}

		let deviceModule = device?.modules.find((m) => m.type === module.type);

		if (device && deviceModule) {
			if (value !== undefined && value !== null) {
				deviceModule.settings[settingKey] = value;
			} else {
				delete deviceModule.settings[settingKey];
			}
		}

		saveState(data.state);
	};

	let selectedModulesValidSettingkeys: string[] = [];
	$: if (selectedModule) {
		console.log(selectedModule);
		selectedModulesValidSettingkeys = Object.keys(selectedModule.settings);
		selectedModulesValidSettingkeys.sort(
			(a, b) => selectedModule.settings[a].order - selectedModule.settings[b].order
		);
		console.log(selectedModulesValidSettingkeys);
	}

	const otherUrlParams = (searchParams: string) => {
		const params = new URLSearchParams(searchParams);
		params.delete('module');
		return params.toString();
	};
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">
		{#if tag}
			{$t('config.header.tag-module', {
				values: { module: selectedModule?.displayName, tag: tag.displayName }
			})}
		{:else if device}
			{$t('config.header.device-module', {
				values: { module: selectedModule?.displayName, device: device.displayName }
			})}
		{:else}
			{$t('config.header.module', { values: { module: selectedModule?.displayName } })}
		{/if}
	</h1>
	<DeployActions />
</div>
<div class="flex gap-10 mb-4">
	<Button href="/config-overview?{otherUrlParams($page.url.search)}">{$t('config.back')}</Button>
	{#if modules.find((m) => m.type === selectedModule?.type)}
		<Button
			on:click={() => {
				if (selectedModule) removeModule(selectedModule);
			}}
		>
			{$t('config.uninstall')}
		</Button>
	{:else}
		<Button
			on:click={() => {
				if (selectedModule) addModule(selectedModule);
			}}
		>
			{$t('config.install')}
		</Button>
	{/if}
</div>
<div class="grid grid-flow-row grid-cols-5 gap-4">
	<Card class="col-span-4 max-w-none grid grid-cols-4 gap-8 gap-x-10 ">
		{#if selectedModule}
			{#each selectedModulesValidSettingkeys as settingKey}
				{@const setting = getSetting(selectedModule, settingKey, tag, device)}
				{@const effectingSettings = getSettings(selectedModule, settingKey, tag, device)}
				<P class="col-span-1">
					{$t(`options.nix.${selectedModule.settings[settingKey].name}`, {
						default: selectedModule.settings[settingKey].name
					})}
				</P>
				<div class="col-span-1 flex">
					<div class="flex-1">
						{#if selectedModule.settings[settingKey].type == 'bool'}
							<ConfigBool
								value={setting === true}
								name={selectedModule.settings[settingKey].name}
								change={(value) => {
									if (selectedModule) setSetting(selectedModule, settingKey, value);
								}}
							/>
						{:else if selectedModule.settings[settingKey].type == 'string'}
							<ConfigString
								value={setting}
								placeholder={selectedModule.settings[settingKey].default}
								change={(value) => {
									if (selectedModule) setSetting(selectedModule, settingKey, value);
								}}
							/>
						{:else if selectedModule.settings[settingKey].type == 'textarea'}
							<ConfigTextarea
								value={setting}
								placeholder={selectedModule.settings[settingKey].default}
								change={(value) => {
									if (selectedModule) setSetting(selectedModule, settingKey, value);
								}}
							/>
						{:else if selectedModule.settings[settingKey].type == 'select-one'}
							<ConfigSelectOne
								value={setting}
								options={selectedModule.settings[settingKey].options}
								setting={selectedModule.settings[settingKey]}
								change={(value) => {
									if (selectedModule) setSetting(selectedModule, settingKey, value);
								}}
							/>
						{/if}
					</div>
					{#if effectingSettings && effectingSettings.length >= 1}
						<div class="mt-1.5 ml-2">
							<button class="btn p-0">
								<Info color="#0080c0" />
							</button>
							<Tooltip>
								{#each effectingSettings.reverse() as effectingSetting}
									<p>{effectingSetting.origin}: {effectingSetting.settings[settingKey]}</p>
								{/each}
							</Tooltip>
							{#if effectingSettings.reverse()[0].origin == getOrigin(tag ?? device)}
								<button
									class="btn p-0"
									on:click={() => {
										if (selectedModule) setSetting(selectedModule, settingKey, undefined);
									}}
									><RotateCcw color="#0080c0" />
								</button>
							{/if}
						</div>
					{/if}
				</div>
				<P class="col-span-2">{selectedModule.settings[settingKey].description}</P>
			{:else}
				<div class="col-span-1">{$t('options.no-settings')}</div>
			{/each}
		{/if}
	</Card>
</div>
