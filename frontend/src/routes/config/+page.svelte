<script lang="ts">
	import { SlideToggle, popup } from '@skeletonlabs/skeleton';
	import { ListBox, ListBoxItem, type PopupSettings } from '@skeletonlabs/skeleton';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import ConfigTextarea from '$lib/config/ConfigTextarea.svelte';
	import type { PageData } from './$types';
	import { queryParam } from 'sveltekit-search-params';
	import { saveState, type Module, type Tag, type Device } from '$lib/state';
	import { page } from '$app/stores';
	// import { Info, RotateCcw, Tag as TagIcon, HardDrive, ChevronDown } from 'lucide-svelte';
	import Info from 'lucide-svelte/icons/info';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import TagIcon from 'lucide-svelte/icons/tag';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';

	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});

	export let data: PageData;

	// $: tagParam = $page.url.searchParams.get('tag');
	// $: deviceParam = $page.url.searchParams.get('device');
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
		return data.availableModules.filter((m) => settings?.find((s) => s.type === m.type));
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

	const selectCombobox: PopupSettings = {
		event: 'click',
		target: 'selectCombobox',
		placement: 'bottom'
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

<div class="grid grid-flow-row grid-cols-5 gap-12">
	<div>
		<div>
			<!-- first text -->
			<h1 class="text-3xl font-bold text-gray-800 mb-4">Select a device or tag</h1>
			<button class="btn variant-filled w-full justify-between" use:popup={selectCombobox}>
				<div class="flex">
					{#if tag}
						<TagIcon class="mr-2" /> {tag.name}
					{:else if device}
						<HardDrive class="mr-2" /> {device.displayName}: {device.hostname}
					{/if}
				</div>
				<span><ChevronDown /></span>
			</button>
			<div class="card w-80 shadow-xl py-2 z-50" data-popup="selectCombobox">
				<ListBox rounded="rounded-none">
					{#each data.state.tags as tag}
						<!-- <a href="/config?tag={tag.name}"> -->
						<a
							href="#"
							on:click={() => {
								$tagParam = tag.name;
								$deviceParam = null;
							}}
						>
							<ListBoxItem
								group={''}
								value={tag.name}
								name={tag.name}
								hover={'hover:variant-filled'}
								active={''}
							>
								<svelte:fragment slot="lead"><TagIcon /></svelte:fragment>
								{tag.name}
							</ListBoxItem>
						</a>
					{/each}
					{#each data.state.devices as device}
						<!-- <a href="/config?device={device.hostname}"> -->
						<a
							href="#"
							on:click={() => {
								$deviceParam = device.hostname;
								$tagParam = null;
							}}
						>
							<ListBoxItem
								group={''}
								value={device.hostname}
								name={device.hostname}
								hover={'hover:variant-filled'}
								active={''}
							>
								<svelte:fragment slot="lead"><HardDrive /></svelte:fragment>
								{device.displayName}: {device.hostname}
							</ListBoxItem>
						</a>
					{/each}
				</ListBox>
			</div>
		</div>
		<div class="mt-8">
			<ListBox>
				{#each data.availableModules as module, i}
					<ListBoxItem
						class="card"
						bind:group={$selected}
						value={i}
						name={module.name}
						active={'bg-primary-500'}
					>
						<div class="flex gap-4 mt-2 mb-2">
							<SlideToggle
								name=""
								size="sm"
								checked={modules.find((m) => m.type === module.type) !== undefined}
								on:change={() => {
									if (modules.find((m) => m.type === module.type) !== undefined) {
										removeModule(module);
									} else {
										addModule(module);
									}
								}}
							/>
							<div>{module.name}</div>
						</div>
					</ListBoxItem>
				{/each}
			</ListBox>
		</div>
	</div>
	<div class="col-span-4 grid grid-cols-4 gap-8 gap-x-10">
		<div class="col-span-4">
			<class class="text-3xl font-bold text-gray-800 mb-4">Module {selectedModule?.name}</class>
		</div>
		{#if $selected != null && $selected < data.availableModules.length}
			{@const selectedModule = data.availableModules[$selected]}
			<!-- {#each Object.keys(selectedModule) as settingKey} -->
			<!-- {#if settingKey !== 'name' && settingKey !== 'type' && typeof selectedModule[settingKey] === 'object'} -->
			{#each selectedModulesValidSettingkeys as settingKey}
				{#if selectedModule && settingKey in selectedModule}
					{@const setting = getSetting(selectedModule, settingKey, tag, device)}
					{@const effectingSettings = getSettings(selectedModule, settingKey, tag, device)}
					{@const popupHover = {
						event: 'hover',
						target: `popupHover-${settingKey}`,
						placement: 'top'
					}}
					<div class="col-span-1">{selectedModule[settingKey].name}</div>
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
								<button class="btn p-0 [&>*]:pointer-events-none" use:popup={popupHover}>
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
				<div class="col-span-1">No settings found for this module</div>
			{/each}
		{/if}
	</div>
</div>
