<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Module, ModuleSettings, ModuleSettingsWithOrigin, Origin } from '$lib/state';
	import { Card, P, Tooltip } from 'flowbite-svelte';
	import Route from 'lucide-svelte/icons/route';
	import RouteOff from 'lucide-svelte/icons/route-off';
	import X from 'lucide-svelte/icons/x';
	import Pen from 'lucide-svelte/icons/pen';
	import DefinitionLine from './DefinitionLine.svelte';
	import ConfigDrawer from './ConfigDrawer.svelte';

	export let module: Module;
	export let settings: ModuleSettingsWithOrigin | undefined;
	export let otherSettings: ModuleSettingsWithOrigin[] | undefined;
	export let showRouting: boolean;
	export let canEdit: boolean;

	export let setSetting: (module: ModuleSettings | Module, settingKey: string, value: any) => void;

	const sameOrigin = (a: Origin | undefined, b: Origin | undefined) => {
		return a?.originId === b?.originId && a?.originContext === b?.originContext;
	};

	const settingsOrder = (a: ModuleSettingsWithOrigin, b: ModuleSettingsWithOrigin) => {
		if (a.priority === undefined && b.priority !== undefined) return -1;
		if (b.priority === undefined && a.priority !== undefined) return 1;
		return (b.priority ?? 0) - (a.priority ?? 0);
	};

	$: settingEntries = Object.entries(module.settings).sort((a, b) => a[1].order - b[1].order);
</script>

<Card class="max-w-none grid grid-cols-4 gap-8">
	{#each settingEntries as [key, setting]}
		{@const self = settings?.settings[key]}
		{@const other = otherSettings
			?.filter((o) => o?.type === module?.type && key in o.settings)
			?.sort(settingsOrder)
			?.map((o) => ({
				...o,
				setting: o.settings[key]
			}))}
		<P class="col-span-1">
			{$t(`options.nix.${setting.name}`, { default: setting.name })}
		</P>
		<div class="col-span-1 flex">
			<div class="flex-1">
				<ConfigDrawer
					{setting}
					value={settings?.settings[key]}
					disabled={!canEdit}
					onChange={(value) => setSetting(module, key, value)}
				/>
			</div>
			{#if canEdit}
				{#if settings?.settings[key] !== undefined}
					<button
						class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
						on:click={() => setSetting(module, key, null)}
					>
						<X />
					</button>
					<Tooltip type="auto"><P size="sm">{$t('config.clear')}</P></Tooltip>
				{:else}
					<button
						class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
						on:click={() => setSetting(module, key, '')}
					>
						<Pen />
					</button>
					<Tooltip type="auto"><P size="sm">{$t('config.edit')}</P></Tooltip>
				{/if}
			{/if}
			{#if showRouting}
				{#if other && other.length > 0}
					{#if sameOrigin(settings, other[0])}
						{@const otherDefinitions = other.filter((o) => !sameOrigin(settings, o))}
						<button class="btn p-0 ml-2" on:click={() => {}}>
							<Route class="text-primary-500" />
						</button>
						<Tooltip type="auto" class="z-50">
							<P size="sm" class="whitespace-pre-line">{$t('config.passed')}</P>
							{#if otherDefinitions?.length > 0}
								<P size="sm" class="whitespace-pre-line mt-2">{$t('config.otherDefinitions')}</P>
								<div class="grid grid-cols-2 gap-x-4">
									{#each otherDefinitions as otherDefinition}
										<DefinitionLine origin={otherDefinition} value={otherDefinition.setting} />
									{/each}
								</div>
							{:else}
								<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
							{/if}
						</Tooltip>
					{:else}
						{@const otherDefinitions = other.filter(
							(o) => !sameOrigin(o, settings) && !sameOrigin(o, other[0])
						)}
						<button class="btn p-0 ml-2" on:click={() => {}}>
							<RouteOff class="text-primary-500" />
						</button>
						<Tooltip type="auto" class="z-50">
							<P size="sm" class="whitespace-pre-line">{@html $t('config.notPassed')}</P>
							<P size="sm" class="whitespace-pre-line mt-2">{$t('config.overwrittenBy')}</P>
							<div class="grid grid-cols-2 gap-x-4">
								<DefinitionLine origin={other[0]} value={other[0].setting} />
							</div>
							{#if otherDefinitions?.length > 0}
								<P size="sm" class="whitespace-pre-line mt-4">{$t('config.otherDefinitions')}</P>
								<div class="grid grid-cols-2 gap-x-4">
									{#each otherDefinitions as otherDefinition}
										<DefinitionLine origin={otherDefinition} value={otherDefinition.setting} />
									{/each}
								</div>
							{/if}
						</Tooltip>
					{/if}
				{:else if self !== undefined}
					<button class="btn p-0 ml-2" on:click={() => {}}>
						<Route class="text-primary-500" />
					</button>
					<Tooltip type="auto" class="z-50">
						<P size="sm" class="whitespace-pre-line">{@html $t('config.passed')}</P>
						<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
					</Tooltip>
				{:else}
					<button class="btn p-0 ml-2" on:click={() => {}}>
						<RouteOff class="text-primary-500" />
					</button>
					<Tooltip type="auto" class="z-50">
						<P size="sm" class="whitespace-pre-line">{@html $t('config.notSet')}</P>
						<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
					</Tooltip>
				{/if}
			{/if}
		</div>
		<P class="col-span-2">{setting.description}</P>
	{:else}
		<div class="col-span-1">{$t('options.no-settings')}</div>
	{/each}
</Card>
