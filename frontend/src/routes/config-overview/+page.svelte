<script lang="ts">
	import { t } from 'svelte-i18n';
	import { P } from 'flowbite-svelte';
	import { queryParam } from 'sveltekit-search-params';
	import type { Tag, Device, Module, ModuleDefinition } from '$lib/state';
	import { saveState } from '$lib/state';

	import DeployActions from '$lib/DeployActions.svelte';
	import ModuleCard from '$lib/ModuleCard.svelte';
	import type { PageData } from './$types';

	export let data: PageData;

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = data.state.tags.find((t) => t.identifier === $tagParam);
	$: device = data.state.devices.find((d) => d.identifier === $deviceParam);
	$: modules = getModules(tag, device);
	$: modulesAnywhere = getModulesInstalledAnywhere();

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

	const getModulesInstalledAnywhere = () => {
		const tagModules = data.state.tags.flatMap((tag) => getModules(tag, undefined));
		const deviceModules = data.state.devices.flatMap((device) => getModules(undefined, device));
		return [...new Set(tagModules.concat(deviceModules))];
	};

	const addModule = (module: Module | ModuleDefinition) => {
		if (tag && !tag.modules.find((m) => m.type === module.type)) {
			tag.modules = [...tag.modules, { type: module.type, settings: {} }];
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
			{$t('config.header.tag-overview', { values: { tag: tag.displayName } })}
		{:else if device}
			{$t('config.header.device-overview', { values: { device: device.displayName } })}
		{:else}
			{$t('config.header.overview')}
		{/if}
	</h1>
	<DeployActions />
</div>
<div>
	<P class="mb-2">{$t('config.section.installed')}</P>
	<div class="flex flex-wrap gap-2">
		{#each modules as module}
			<ModuleCard {module} installed={true} {addModule} />
		{/each}
	</div>
</div>
<div class="mt-8">
	<P class="mb-2">{$t('config.section.installed-elsewhere')}</P>
	<div class="flex flex-wrap gap-2">
		{#each modulesAnywhere as module}
			{#if !modules.find((m) => m.type === module.type)}
				<ModuleCard {module} installed={false} {addModule} />
			{/if}
		{/each}
	</div>
</div>
<div class="mt-8">
	<P class="mb-2">{$t('config.section.available')}</P>
	<div class="flex flex-wrap gap-2">
		{#each data.availableModules as module}
			{#if !modules.find((m) => m.type === module.type) && !modulesAnywhere.find((m) => m.type === module.type)}
				<ModuleCard {module} installed={false} {addModule} />
			{/if}
		{/each}
	</div>
</div>
