<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState } from '$lib/state';
	import type {
		ContextType,
		Module,
		ModuleSettingsWithOrigin,
		Origin,
		Setting,
		SettingType
	} from '$lib/state';
	import { Card, P, Tooltip } from 'flowbite-svelte';
	import Route from 'lucide-svelte/icons/route';
	import RouteOff from 'lucide-svelte/icons/route-off';
	import X from 'lucide-svelte/icons/x';
	import Pen from 'lucide-svelte/icons/pen';
	import Copy from 'lucide-svelte/icons/copy';
	import Paste from 'lucide-svelte/icons/clipboard-copy';
	import DefinitionLine from './DefinitionLine.svelte';
	import ConfigRenderer from './ConfigRenderer.svelte';
	import { configSelectedModuleContext } from '$lib/searchParamHelpers';

	export let module: Module;
	export let settings: ModuleSettingsWithOrigin | undefined;
	export let configSelectedModuleContextType: ContextType;
	export let otherSettings: ModuleSettingsWithOrigin[] | undefined;
	export let showRouting: boolean;
	export let canEdit: boolean;

	const setSetting = async (setting: Setting<SettingType>, settingKey: string, value: any) => {
		if ($configSelectedModuleContext && settings) {
			if (value !== undefined && value !== null) {
				settings.settings[settingKey] = value;
			} else {
				delete settings.settings[settingKey];
			}
		}

		await saveState();
	};

	const sameOrigin = (a: Origin | undefined, b: Origin | undefined) => {
		return a?.originId === b?.originId && a?.originContext === b?.originContext;
	};

	const settingsOrder = (a: ModuleSettingsWithOrigin, b: ModuleSettingsWithOrigin) => {
		if (a.priority === undefined && b.priority !== undefined) return -1;
		if (b.priority === undefined && a.priority !== undefined) return 1;
		return (b.priority ?? 0) - (a.priority ?? 0);
	};

	$: settingEntries = Object.entries(module.settings).sort((a, b) => a[1].order - b[1].order);

	const canReallyEditSetting = (canEdit: boolean, setting: Setting) =>
		canEdit &&
		!(
			setting &&
			typeof setting.type === 'object' &&
			'extra_data' in setting.type &&
			typeof setting.type.extra_data === 'object' &&
			setting.type.extra_data &&
			'only_editable_on_target_type' in setting.type.extra_data &&
			Array.isArray(setting.type.extra_data.only_editable_on_target_type) &&
			!setting.type.extra_data.only_editable_on_target_type.includes(
				configSelectedModuleContextType
			)
		);

	const canPaste = (clipboardText: string, setting: Setting<SettingType>) => {
		if (clipboardText === undefined) return;
		const parsed = JSON.parse(clipboardText);
		return (
			setting.type === typeof parsed.value ||
			JSON.stringify(parsed.type) === JSON.stringify(setting.type)
		);
	};
</script>

<Card
	class="max-w-none grid grid-cols-[minmax(50px,3fr)_1fr] sm:grid-cols-[auto_250px] xl:grid-cols-[auto_350px] gap-4"
	padding={'sm'}
>
	{#each settingEntries as [key, setting]}
		{@const self = settings?.settings[key]}
		{@const other = otherSettings
			?.filter((o) => o?.type === module?.type && key in o.settings)
			?.sort(settingsOrder)
			?.map((o) => ({
				...o,
				setting: o.settings[key]
			}))}
		<div class="flex flex-col">
			<P class="mb-1">
				{$t(setting.displayName)}
			</P>
			<div class="flex gap-1">
				<ConfigRenderer
					{setting}
					moduleSettings={settings}
					value={settings?.settings[key]}
					disabled={!canReallyEditSetting(canEdit, setting)}
					onChange={(value) => setSetting(setting, key, value)}
				/>
				<div class="ml-auto" />
				<button
					class="m-0 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
					on:click={async (e) =>
						await navigator.clipboard.writeText(
							JSON.stringify({ type: setting.type, value: settings?.settings[key] })
						)}
					disabled={!settings?.settings[key]}
				>
					<Copy size="20" />
				</button>
				<Tooltip type="auto">{$t('config.copy')}</Tooltip>
				{#if canEdit}
					<button
						class="m-0 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
						on:click={async () => {
							const clipboardText = await navigator.clipboard.readText();
							if (canPaste(clipboardText, setting)) {
								setSetting(setting, key, JSON.parse(clipboardText).value);
							}
						}}
					>
						<Paste size="20" />
					</button>
					<Tooltip type="auto">{$t('config.paste')}</Tooltip>
				{/if}
				{#if canEdit}
					{#if settings?.settings[key] !== undefined}
						<button
							class="m-0 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
							on:click={() => setSetting(setting, key, null)}
						>
							<X size="20" />
						</button>
						<Tooltip type="auto">{$t('config.clear')}</Tooltip>
					{:else if canReallyEditSetting(canEdit, setting)}
						<button
							class="m-0 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
							on:click={() =>
								setSetting(
									setting,
									key,
									typeof setting.type === 'object' && setting.type.hasOwnProperty('list-of')
										? []
										: ''
								)}
						>
							<Pen size="20" />
						</button>
						<Tooltip type="auto">{$t('config.edit')}</Tooltip>
					{/if}
				{/if}
				{#if showRouting}
					{#if other && other.length > 0}
						{#if sameOrigin(settings, other[0])}
							{@const otherDefinitions = other.filter((o) => !sameOrigin(settings, o))}
							<button class="m-0 p-1" on:click={() => {}}>
								<Route class="text-primary-600 dark:text-primary-400" size="20" />
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
									<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P
									>
								{/if}
							</Tooltip>
						{:else}
							{@const otherDefinitions = other.filter(
								(o) => !sameOrigin(o, settings) && !sameOrigin(o, other[0])
							)}
							<button class="m-0 p-1" on:click={() => {}}>
								<RouteOff class="text-primary-600 dark:text-primary-400" size="20" />
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
						<button class="m-0 p-1" on:click={() => {}}>
							<Route class="text-primary-600 dark:text-primary-400" size="20" />
						</button>
						<Tooltip type="auto" class="z-50">
							<P size="sm" class="whitespace-pre-line">{@html $t('config.passed')}</P>
							<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
						</Tooltip>
					{:else}
						<button class="m-0 p-1" on:click={() => {}}>
							<RouteOff class="text-primary-600 dark:text-primary-400" size="20" />
						</button>
						<Tooltip type="auto" class="z-50">
							<P size="sm" class="whitespace-pre-line">{@html $t('config.notSet')}</P>
							<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
						</Tooltip>
					{/if}
				{/if}
			</div>
		</div>
		<P class="mt-[1.9rem] whitespace-pre-line">{setting.description}</P>
	{:else}
		<div>{$t('config.no-settings')}</div>
	{/each}
</Card>
