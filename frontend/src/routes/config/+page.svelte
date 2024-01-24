<script lang="ts">
	import { ListBox, ListBoxItem } from '@skeletonlabs/skeleton';
	import ConfigBool from '$lib/config/ConfigBool.svelte';
	import ConfigString from '$lib/config/ConfigString.svelte';
	import type { PageData } from './$types';
	import { queryParam } from 'sveltekit-search-params';
	import { saveState, type Module } from '$lib/state';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';

	const selected = queryParam<number>('selected', {
		decode: (value) => (value ? parseInt(value, 10) : 0),
		encode: (value) => value.toString()
	});

	export let data: PageData;
	$: state = data.state;

	let tagParam = $page.url.searchParams.get('tag');
	let deviceParam = $page.url.searchParams.get('device');

	$: tag = state.tags.find((t) => t.name === tagParam);
	$: device = state.devices.find((d) => d.hostname === deviceParam);

	$: getModuleSettings = () => {
		if (tag) {
			return tag.modules;
		}

		if (device) {
			return [
				...device.modules,
				...device.tags.flatMap((t) => state.tags.find((tag) => tag.name === t)?.modules ?? [])
			];
		}
	};

	$: getModules = () => {
		let settings = getModuleSettings();
		return data.availableModules.filter((m) => settings?.find((s) => s.type === m.type));
	};

	$: addModule = (module: Module) => {
		if (tag && !tag.modules.find((m) => m.type === module.type)) {
			tag.modules.push({ type: module.type, priority: 5, settings: {} });
		}

		if (device && !device.modules.find((m) => m.type === module.type)) {
			device.modules.push({ type: module.type, settings: {} });
		}
	};

	$: removeModule = (module: Module) => {
		if (tag) {
			tag.modules = tag.modules.filter((m) => m.type !== module.type);
		}

		if (device) {
			device.modules = device.modules.filter((m) => m.type !== module.type);
		}
	};

	$: getSetting = (module: Module, settingKey: string) => {
		let settings = getModuleSettings();
		return settings?.find(
			(s) => s.type === module.type && Object.keys(s.settings).includes(settingKey)
		)?.settings[settingKey].value as any;
	};

	$: setSetting = (module: Module, settingKey: string, value: any) => {
		addModule(module);

		if (tag) {
			let tagModule = tag.modules.find((m) => m.type === module.type);
			if (tagModule) {
				tagModule.settings[settingKey] = { ...tagModule.settings[settingKey], value: value };
			}
		}

		if (device) {
			let deviceModule = device.modules.find((m) => m.type === module.type);
			if (deviceModule) {
				deviceModule.settings[settingKey] = { ...deviceModule.settings[settingKey], value: value };
			}
		}
	};

	$: modules = getModules();
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
									$selected = null;
								}}
							>
								delete
							</button>
						</div>
					</ListBoxItem>
				{/each}
			</ListBox>
		</div>
		<div class="mt-6">
			<button type="button" class="btn variant-filled mt-8" on:click={() => saveState(state)}>
				save
			</button>
		</div>
	</div>
	<div class="col-span-4 grid grid-cols-4 gap-8 gap-x-10">
		{#if $selected != null && $selected < modules.length}
			{#each Object.keys(modules[$selected]) as settingKey}
				{#if settingKey !== 'name' && settingKey !== 'type'}
					<div class="col-span-1">{modules[$selected][settingKey].name}</div>
					<div class="col-span-1">
						{#if modules[$selected][settingKey].type == 'bool'}
							<ConfigBool
								value={getSetting(modules[$selected], settingKey)}
								name={modules[$selected][settingKey].name}
								onChange={(value) => {
									if ($selected != null) setSetting(modules[$selected], settingKey, value);
								}}
							/>
						{:else if modules[$selected][settingKey].type == 'string'}
							<ConfigString
								value={getSetting(modules[$selected], settingKey)}
								placeholder={modules[$selected][settingKey].default}
								onChange={(value) => {
									if ($selected != null) setSetting(modules[$selected], settingKey, value);
								}}
							/>
						{/if}
					</div>
					<div class="col-span-2">{modules[$selected][settingKey].description}</div>
				{/if}
			{/each}
		{/if}
	</div>
</div>
