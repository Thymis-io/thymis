<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Module, ModuleSettings, ModuleSettingsWithOrigin, Origin } from '$lib/state';
	import { Card, P, Tooltip } from 'flowbite-svelte';
	import ConfigString from './ConfigString.svelte';
	import ConfigBool from './ConfigBool.svelte';
	import ConfigTextarea from './ConfigTextarea.svelte';
	import ConfigSelectOne from './ConfigSelectOne.svelte';
	import { Route } from 'lucide-svelte';
	import { RouteOff } from 'lucide-svelte';
	import { X } from 'lucide-svelte';
	import DefinitionLine from './DefinitionLine.svelte';

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

	const settingEntries = Object.entries(module.settings).sort((a, b) => a[1].order - b[1].order);
</script>

<Card class="max-w-none grid grid-cols-4 gap-8">
	{#each settingEntries as [key, setting]}
		{@const self = settings?.settings[key]}
		{@const other = otherSettings
			?.filter((o) => o?.type === module?.type && key in o.settings)
			?.sort(settingsOrder)
			?.map((o) => ({
				...o,
				options: module.settings[key].options,
				setting: o.settings[key]
			}))}
		<P class="col-span-1">
			{$t(`options.nix.${setting.name}`, { default: setting.name })}
		</P>
		<div class="col-span-1 flex">
			<div class="flex-1">
				{#if setting.type == 'bool'}
					<ConfigBool
						value={settings?.settings[key] === true}
						name={setting.name}
						change={(value) => {
							setSetting(module, key, value);
						}}
						disabled={!canEdit}
					/>
				{:else if setting.type == 'string'}
					<ConfigString
						value={settings?.settings[key]}
						placeholder={setting.default}
						change={(value) => {
							setSetting(module, key, value);
						}}
						disabled={!canEdit}
					/>
				{:else if setting.type == 'textarea'}
					<ConfigTextarea
						value={settings?.settings[key]}
						placeholder={setting.default}
						change={(value) => {
							setSetting(module, key, value);
						}}
						disabled={!canEdit}
					/>
				{:else if setting.type == 'select-one'}
					<ConfigSelectOne
						value={settings?.settings[key]}
						options={setting.options}
						{setting}
						change={(value) => {
							setSetting(module, key, value);
						}}
						disabled={!canEdit}
					/>
				{/if}
			</div>
			{#if canEdit && settings?.settings[key]}
				<button
					class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
					on:click={() => setSetting(module, key, null)}
				>
					<X class="" />
				</button>
				<Tooltip><P size="sm">{$t('config.clear')}</P></Tooltip>
			{/if}
			{#if showRouting && other && other.length > 0}
				{#if sameOrigin(settings, other[0])}
					{@const otherDefinitions = other.filter((o) => !sameOrigin(settings, o))}
					<button class="btn p-0 ml-2" on:click={() => {}}><Route color="#0080c0" /></button>
					<Tooltip>
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
					<button class="btn p-0 ml-2" on:click={() => {}}><RouteOff color="#0080c0" /></button>
					<Tooltip>
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
			{/if}
		</div>
		<P class="col-span-2">{setting.description}</P>
	{:else}
		<div class="col-span-1">{$t('options.no-settings')}</div>
	{/each}
</Card>
