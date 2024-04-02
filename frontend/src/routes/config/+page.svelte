<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card, Toggle, Listgroup, ListgroupItem, Tooltip, P, Button } from 'flowbite-svelte';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import ConfigTextarea from '$lib/config/ConfigTextarea.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import { saveState } from '$lib/state';
	import type { Module, Tag, Device } from '$lib/state';

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

	let modules: Module[];

	$: tag = data.state.tags.find((t) => t.identifier === $tagParam);
	$: device = data.state.devices.find((d) => d.identifier === $deviceParam);
	$: modules = getModules(tag, device);
	$: selectedModule = data.availableModules.find((m) => m.type === $moduleParam);

	const getOrigin = (tag: Tag | undefined, device: Device | undefined) => {
		if (tag) {
			return tag.displayName;
		}

		if (device) {
			return device.displayName;
		}
	};

	const getModuleSettings = (tag: Tag | undefined, device: Device | undefined) => {
		if (tag) {
			return tag.modules.map((m) => ({ origin: getOrigin(tag, undefined), ...m }));
		}

		if (device) {
			let usedTags = device.tags.flatMap(
				(t) => data.state.tags.find((tag) => tag.displayName === t) ?? []
			);
			return [
				...device.modules.map((m) => ({ origin: getOrigin(undefined, device), ...m })),
				...usedTags.flatMap((t) =>
					t.modules.map((m) => ({ origin: getOrigin(t, undefined), ...m }))
				)
			];
		}
	};

	const getModules = (tag: Tag | undefined, device: Device | undefined) => {
		let settings = getModuleSettings(tag, device);
		return data.availableModules.filter((m) => settings?.find((s) => s.type === m.type)) ?? [];
	};

	const addModule = (module: Module) => {
		if (tag && !tag.modules.find((m) => m.type === module.type)) {
			tag.modules = [...tag.modules, { type: module.type, priority: 5, settings: {} }];
		}

		if (device && !device.modules.find((m) => m.type === module.type)) {
			device.modules = [...device.modules, { type: module.type, settings: {} }];
		}

		saveState(data.state);
	};

	const removeModule = (module: Module) => {
		if (tag) {
			tag.modules = tag.modules.filter((m) => m.type !== module.type);
		}

		if (device) {
			device.modules = device.modules.filter((m) => m.type !== module.type);
		}

		saveState(data.state);
	};

	const getSettings = (
		module: Module,
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
		module: Module,
		settingKey: string,
		tag: Tag | undefined,
		device: Device | undefined
	) => {
		let settings = getSettings(module, settingKey, tag, device);

		if (settings && settings.length >= 1) {
			return settings[0].settings[settingKey].value;
		}
	};

	const setSetting = (module: Module, settingKey: string, value: any) => {
		addModule(module);

		let tagModule = tag?.modules.find((m) => m.type === module.type);

		if (tag && tagModule) {
			if (value !== undefined && value !== null) {
				tagModule.settings[settingKey] = { ...tagModule.settings[settingKey], value: value };
			} else {
				delete tagModule.settings[settingKey];
			}
		}

		let deviceModule = device?.modules.find((m) => m.type === module.type);

		if (device && deviceModule) {
			if (value !== undefined && value !== null) {
				deviceModule.settings[settingKey] = {
					...deviceModule.settings[settingKey],
					value: value
				};
			} else {
				delete deviceModule.settings[settingKey];
			}
		}

		saveState(data.state);
	};

	let selectedModulesValidSettingkeys: string[] = [];
	$: if (selectedModule) {
		console.log(selectedModule);
		selectedModulesValidSettingkeys = Object.keys(selectedModule).filter(
			(settingKey) =>
				settingKey &&
				settingKey !== 'name' &&
				settingKey !== 'type' &&
				selectedModule &&
				typeof selectedModule[settingKey] === 'object' &&
				selectedModule[settingKey] &&
				'name' in selectedModule[settingKey]
		);
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
				values: { module: selectedModule?.name, tag: tag.displayName }
			})}
		{:else if device}
			{$t('config.header.device-module', {
				values: { module: selectedModule?.name, device: device.displayName }
			})}
		{:else}
			{$t('config.header.module', { values: { module: selectedModule?.name } })}
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
				{#if settingKey in selectedModule}
					{@const setting = getSetting(selectedModule, settingKey, tag, device)}
					{@const effectingSettings = getSettings(selectedModule, settingKey, tag, device)}
					<P class="col-span-1">
						{$t(`options.nix.${selectedModule[settingKey].name}`, {
							default: selectedModule[settingKey].name
						})}
					</P>
					<div class="col-span-1 flex">
						<div class="flex-1">
							{#if selectedModule[settingKey].type == 'bool'}
								<ConfigBool
									value={setting}
									name={selectedModule[settingKey].name}
									change={(value) => {
										if (selectedModule) setSetting(selectedModule, settingKey, value);
									}}
								/>
							{:else if selectedModule[settingKey].type == 'string'}
								<ConfigString
									value={setting}
									placeholder={selectedModule[settingKey].default}
									change={(value) => {
										if (selectedModule) setSetting(selectedModule, settingKey, value);
									}}
								/>
							{:else if selectedModule[settingKey].type == 'textarea'}
								<ConfigTextarea
									value={setting}
									placeholder={selectedModule[settingKey].default}
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
										<p>{effectingSetting.origin}: {effectingSetting.settings[settingKey].value}</p>
									{/each}
								</Tooltip>
								{#if effectingSettings.reverse()[0].origin == getOrigin(tag, device)}
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
					<P class="col-span-2">{selectedModule[settingKey].description}</P>
				{/if}
			{:else}
				<div class="col-span-1">{$t('options.no-settings')}</div>
			{/each}
		{/if}
	</Card>
</div>
