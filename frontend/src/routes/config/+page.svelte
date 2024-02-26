<script lang="ts">
	import { t } from 'svelte-i18n';
	import { SlideToggle, popup } from '@skeletonlabs/skeleton';
	import { Card, Toggle, Listgroup, ListgroupItem } from 'flowbite-svelte';
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

	export let data: PageData;

	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = data.state.tags.find((t) => t.name === $tagParam);
	$: device = data.state.devices.find((d) => d.hostname === $deviceParam);
	$: modules = getModules(tag, device);

	const getOrigin = (tag: Tag | undefined, device: Device | undefined) => {
		if (tag) {
			return tag.name;
		}

		if (device) {
			return device.hostname;
		}
	};

	const getModuleSettings = (tag: Tag | undefined, device: Device | undefined) => {
		if (tag) {
			return tag.modules.map((m) => ({ origin: getOrigin(tag, undefined), ...m }));
		}

		if (device) {
			let usedTags = device.tags.flatMap(
				(t) => data.state.tags.find((tag) => tag.name === t) ?? []
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

	let selectedModule: Module | undefined;
	$: if ($selected != null) {
		selectedModule = data.availableModules[$selected];
	}
	let selectedModulesValidSettingkeys: string[] = [];
	$: if ($selected != null && selectedModule) {
		console.log(selectedModule);
		selectedModulesValidSettingkeys = Object.keys(selectedModule).filter(
			(settingKey) =>
				settingKey !== 'name' &&
				settingKey !== 'type' &&
				selectedModule &&
				typeof selectedModule[settingKey] === 'object' &&
				'name' in selectedModule[settingKey]
		);
	}
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">
		{#if tag}
			Module im Tag verwalten
		{:else if device}
			Module im Gerät verwalten
		{:else}
			Module verwalten
		{/if}
	</h1>
	<div>
		<DeployActions />
	</div>
</div>
<div class="grid grid-flow-row grid-cols-5 gap-4">
	<div>
		<Listgroup active>
			{#each data.availableModules as module, i}
				<ListgroupItem
					on:click={() => ($selected = i)}
					current={$selected === i}
					currentClass="bg-primary-500"
				>
					<div>
						<Toggle
							checked={modules.find((m) => m.type === module.type) !== undefined}
							on:change={() => {
								if (modules.find((m) => m.type === module.type) !== undefined) {
									removeModule(module);
								} else {
									addModule(module);
								}
							}}>{module.name}</Toggle
						>
					</div>
				</ListgroupItem>
			{/each}
		</Listgroup>
	</div>
	<Card class="col-span-4 max-w-none grid grid-cols-4 gap-8 gap-x-10 ">
		{#if $selected != null && $selected < data.availableModules.length}
			{@const selectedModule = data.availableModules[$selected]}
			<!-- {#each Object.keys(selectedModule) as settingKey} -->
			<!-- {#if settingKey !== 'name' && settingKey !== 'type' && typeof selectedModule[settingKey] === 'object'} -->
			{#each selectedModulesValidSettingkeys as settingKey}
				{#if selectedModule && settingKey in selectedModule}
					{@const setting = getSetting(selectedModule, settingKey, tag, device)}
					{@const effectingSettings = getSettings(selectedModule, settingKey, tag, device)}
					<div class="col-span-1">
						<div
							class="pointer-events-none [&>*]:pointer-events-none"
							use:popup={{ event: 'hover', target: `popupKey-${settingKey}`, placement: 'top' }}
						>
							{$t(`options.nix.${selectedModule[settingKey].name}`, {
								default: selectedModule[settingKey].name
							})}
							<div
								class="card p-3 variant-filled-primary z-40 mt-2"
								data-popup="popupKey-{settingKey}"
							>
								<p class="selection:bg-blue-200">{selectedModule[settingKey].name}</p>
								<div class="arrow variant-filled-primary" />
							</div>
						</div>
					</div>
					<div class="col-span-1 flex">
						<div class="flex-1">
							{#if selectedModule[settingKey].type == 'bool'}
								<ConfigBool
									value={setting}
									name={selectedModule[settingKey].name}
									change={(value) => {
										if ($selected != null) setSetting(selectedModule, settingKey, value);
									}}
								/>
							{:else if selectedModule[settingKey].type == 'string'}
								<ConfigString
									value={setting}
									placeholder={selectedModule[settingKey].default}
									change={(value) => {
										if ($selected != null) setSetting(selectedModule, settingKey, value);
									}}
								/>
							{:else if selectedModule[settingKey].type == 'textarea'}
								<ConfigTextarea
									value={setting}
									placeholder={selectedModule[settingKey].default}
									change={(value) => {
										if ($selected != null) setSetting(selectedModule, settingKey, value);
									}}
								/>
							{/if}
						</div>
						{#if effectingSettings && effectingSettings.length >= 1}
							<div class="mt-1.5 ml-2">
								<button
									class="btn p-0 [&>*]:pointer-events-none"
									use:popup={{
										event: 'hover',
										target: `popupHover-${settingKey}`,
										placement: 'top'
									}}
								>
									<Info color="#0080c0" />
								</button>
								<div
									class="card p-4 variant-filled-primary z-40"
									data-popup="popupHover-{settingKey}"
								>
									{#each effectingSettings.reverse() as effectingSetting}
										<p>{effectingSetting.origin}: {effectingSetting.settings[settingKey].value}</p>
									{/each}
									<div class="arrow variant-filled-primary" />
								</div>
								{#if effectingSettings.reverse()[0].origin == getOrigin(tag, device)}
									<button
										class="btn p-0"
										on:click={() => {
											if ($selected != null) setSetting(selectedModule, settingKey, undefined);
										}}
										><RotateCcw color="#0080c0" />
									</button>
								{/if}
							</div>
						{/if}
					</div>
					<div class="col-span-2">{selectedModule[settingKey].description}</div>
				{/if}
			{:else}
				<div class="col-span-1">{$t('options.no-settings')}</div>
			{/each}
		{/if}
	</Card>
</div>
