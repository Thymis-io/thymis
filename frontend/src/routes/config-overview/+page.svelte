<script lang="ts">
	import { t } from 'svelte-i18n';
	import { P } from 'flowbite-svelte';
	import { queryParam } from 'sveltekit-search-params';
	import type { Tag, Device, Module } from '$lib/state';
	import { saveState } from '$lib/state';

	import DeployActions from '$lib/DeployActions.svelte';
	import ModuleCard from '$lib/ModuleCard.svelte';
	import type { PageData } from './$types';

	export let data: PageData;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = data.state.tags.find((t) => t.name === $tagParam);
	$: device = data.state.devices.find((d) => d.hostname === $deviceParam);
	$: modules = getModules(tag, device);
	$: modulesAnywhere = getModulesInstalledAnywhere();

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

	const getModulesInstalledAnywhere = () => {
		const tagModules = data.state.tags.flatMap((tag) => getModules(tag, undefined));
		const deviceModules = data.state.devices.flatMap((device) => getModules(undefined, device));
		return [...new Set(tagModules.concat(deviceModules))];
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
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">
		{#if tag}
			Module im Tag {tag.name} verwalten
		{:else if device}
			Module im Gerät {device.displayName} verwalten
		{:else}
			Module verwalten
		{/if}
	</h1>
	<DeployActions />
</div>
<div>
	<P class="mb-2">Installed</P>
	<div class="flex flex-wrap gap-2">
		{#each modules as module}
			<ModuleCard {module} installed={true} {addModule} />
		{/each}
	</div>
</div>
<div class="mt-8">
	<P class="mb-2">Installed on other devices or tags</P>
	<div class="flex flex-wrap gap-2">
		{#each modulesAnywhere as module}
			{#if !modules.find((m) => m.type === module.type)}
				<ModuleCard {module} installed={false} {addModule} />
			{/if}
		{/each}
	</div>
</div>
<div class="mt-8">
	<P class="mb-2">Available</P>
	<div class="flex flex-wrap gap-2">
		{#each data.availableModules as module}
			{#if !modules.find((m) => m.type === module.type) && !modulesAnywhere.find((m) => m.type === module.type)}
				<ModuleCard {module} installed={false} {addModule} />
			{/if}
		{/each}
	</div>
</div>
