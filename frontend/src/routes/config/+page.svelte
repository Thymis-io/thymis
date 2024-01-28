<script lang="ts">
	import { popup } from '@skeletonlabs/skeleton';
	import { ListBox, ListBoxItem, type PopupSettings } from '@skeletonlabs/skeleton';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import type { PageData } from './$types';
	import { queryParam } from 'sveltekit-search-params';
	import { saveState, type Module, type Tag, type Device } from '$lib/state';
	import { page } from '$app/stores';
	import { Info, RotateCcw } from 'lucide-svelte';

	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});

	export let data: PageData;

	let tagParam = $page.url.searchParams.get('tag');
	let deviceParam = $page.url.searchParams.get('device');

	$: tag = data.state.tags.find((t) => t.name === tagParam);
	$: device = data.state.devices.find((d) => d.hostname === deviceParam);
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
</script>

<div class="grid grid-flow-row grid-cols-5 gap-12">
	<div>
		<div>
			{#if tag}
				Tag: {tag.name}
			{:else if device}
				Device: {device.hostname}
			{/if}
		</div>
		<div class="mt-8">
			Available Modules
			<ListBox>
				{#each data.availableModules.filter((m) => !modules.find((m2) => m2.type === m.type)) as module, i}
					<ListBoxItem group={''} value={i} name={module.name} hover={''} active={''}>
						<div class="flex place-content-between">
							<div>{module.name}</div>
							<button class="btn" on:click={() => addModule(module)}> add </button>
						</div>
					</ListBoxItem>
				{/each}
			</ListBox>
		</div>
		<div class="mt-4">
			Installed Modules
			<ListBox>
				{#each modules as module, i}
					<ListBoxItem bind:group={$selected} value={i} name={module.name}>
						<div class="flex place-content-between">
							<div>{module.name}</div>
							<button
								class="btn"
								on:click={() => {
									removeModule(module);

									if ($selected && getModules(tag, device).length > 0) {
										$selected = Math.max(0, $selected - 1);
									} else {
										$selected = null;
									}
								}}
							>
								delete
							</button>
						</div>
					</ListBoxItem>
				{/each}
			</ListBox>
		</div>
	</div>
	<div class="col-span-4 grid grid-cols-4 gap-8 gap-x-10">
		{#if $selected != null && $selected < modules.length}
			{#each Object.keys(modules[$selected]) as settingKey}
				{#if settingKey !== 'name' && settingKey !== 'type'}
					{@const setting = getSetting(modules[$selected], settingKey, tag, device)}
					{@const effectingSettings = getSettings(modules[$selected], settingKey, tag, device)}
					{@const popupHover = {
						event: 'hover',
						target: `popupHover-${settingKey}`,
						placement: 'top'
					}}
					<div class="col-span-1">{modules[$selected][settingKey].name}</div>
					<div class="col-span-1 flex">
						<div class="flex-1">
							{#if modules[$selected][settingKey].type == 'bool'}
								<ConfigBool
									value={setting}
									name={modules[$selected][settingKey].name}
									change={(value) => {
										if ($selected != null) setSetting(modules[$selected], settingKey, value);
									}}
								/>
							{:else if modules[$selected][settingKey].type == 'string'}
								<ConfigString
									value={setting}
									placeholder={modules[$selected][settingKey].default}
									change={(value) => {
										if ($selected != null) setSetting(modules[$selected], settingKey, value);
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
											if ($selected != null) setSetting(modules[$selected], settingKey, undefined);
										}}
										><RotateCcw color="#0080c0" />
									</button>
								{/if}
							</div>
						{/if}
					</div>
					<div class="col-span-2">{modules[$selected][settingKey].description}</div>
				{/if}
			{/each}
		{/if}
	</div>
</div>
