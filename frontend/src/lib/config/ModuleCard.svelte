<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Module, ModuleSettingsWithOrigin, Origin, Setting, SettingType } from '$lib/state';
	import { P, Tooltip } from 'flowbite-svelte';
	import Route from 'lucide-svelte/icons/route';
	import RouteOff from 'lucide-svelte/icons/route-off';
	import X from 'lucide-svelte/icons/x';
	import Pen from 'lucide-svelte/icons/pen';
	import Copy from 'lucide-svelte/icons/copy';
	import Paste from 'lucide-svelte/icons/clipboard-copy';
	import DefinitionLine from './DefinitionLine.svelte';
	import ConfigRenderer from './ConfigRenderer.svelte';
	import ModuleIcon from './ModuleIcon.svelte';
	import type { Nav } from '../../routes/(authenticated)/+layout';
	import type { GlobalState } from '$lib/state.svelte';
	import type { Artifact } from '../../routes/(authenticated)/artifacts/[...rest]/+page';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		module: Module;
		settings: ModuleSettingsWithOrigin | undefined;
		otherSettings: ModuleSettingsWithOrigin[] | undefined;
		showRouting: boolean;
		canEdit: boolean;
		artifacts: Artifact[];
		shouldLockSetting?: (settingKey: string, setting: Setting) => boolean;
	}

	let {
		nav,
		globalState,
		module,
		settings = $bindable(),
		otherSettings,
		showRouting,
		canEdit,
		artifacts,
		shouldLockSetting = () => false
	}: Props = $props();

	const setSetting = async (setting: Setting<SettingType>, key: string, value: any) => {
		if (globalState.selectedModuleSettings) {
			if (value !== undefined && value !== null) {
				globalState.selectedModuleSettings.settings[key] = value;
			} else {
				delete globalState.selectedModuleSettings.settings[key];
			}
		}

		globalState.save();
	};

	const sameOrigin = (a: Origin | undefined, b: Origin | undefined) => {
		return a?.originId === b?.originId && a?.originContext === b?.originContext;
	};

	const settingsOrder = (a: ModuleSettingsWithOrigin, b: ModuleSettingsWithOrigin) => {
		if (a.priority === undefined && b.priority !== undefined) return -1;
		if (b.priority === undefined && a.priority !== undefined) return 1;
		return (b.priority ?? 0) - (a.priority ?? 0);
	};

	let settingEntries = $derived(
		Object.entries(module.settings).sort((a, b) => a[1].order - b[1].order)
	);

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
			!setting.type.extra_data.only_editable_on_target_type.includes(nav.selectedModuleContextType)
		);

	const canEditSetting = (canEdit: boolean, key: string, setting: Setting) =>
		canReallyEditSetting(canEdit, setting) && !shouldLockSetting(key, setting);

	const canPaste = (clipboardText: string, setting: Setting<SettingType>) => {
		if (clipboardText === undefined) return;
		try {
			const parsed = JSON.parse(clipboardText);
			return (
				setting.type === typeof parsed.value ||
				(parsed.type === 'secret' &&
					typeof setting.type === 'object' &&
					'type' in setting.type &&
					setting.type.type === 'secret' &&
					setting.type['allowed-types'].includes(parsed.secret_type)) ||
				JSON.stringify(parsed.type) === JSON.stringify(setting.type)
			);
		} catch (e) {
			return false;
		}
	};
</script>

<div class="ds-card flex flex-col">
	<div class="ds-card-head">
		<div class="flex min-w-0 items-center gap-3">
			<span class="ds-icon-tile info"><ModuleIcon {module} imageClass="w-[18px]" /></span>
			<h2 class="ds-card-title truncate">{module.displayName}</h2>
		</div>
	</div>
	<div class="ds-card-pad flex flex-col divide-y divide-[var(--ds-border)]">
		{#each settingEntries as [key, setting]}
			{@const self = settings?.settings[key]}
			{@const other = otherSettings
				?.filter((o) => o?.type === module?.type && key in o.settings)
				?.sort(settingsOrder)
				?.map((o) => ({
					...o,
					setting: o.settings[key]
				}))}
			<div class="flex flex-col gap-2 py-4 first:pt-0 last:pb-0">
				<label for="config-{key}" class="ds-form-label">
					{$t(setting.displayName)}
				</label>
				<div class="flex items-start gap-1">
					<div class="min-w-0 flex-1">
						{#key (module.type, globalState.selectedModuleSettings?.settings[key], !canEditSetting(canEdit, key, setting))}
							<ConfigRenderer
								key="config-{key}"
								{setting}
								moduleSettings={settings}
								value={globalState.selectedModuleSettings?.settings[key]}
								disabled={!canEditSetting(canEdit, key, setting)}
								onChange={(value) => setSetting(setting, key, value)}
								{artifacts}
							/>
						{/key}
					</div>
					<button
						class="ds-icon-btn"
						onclick={async (e) =>
							await navigator.clipboard.writeText(
								JSON.stringify({ type: setting.type, value: settings?.settings[key] })
							)}
						disabled={!settings?.settings[key]}
					>
						<Copy size="18" />
					</button>
					<Tooltip type="auto">{$t('config.copy')}</Tooltip>
					{#if canEditSetting(canEdit, key, setting)}
						<button
							class="ds-icon-btn"
							onclick={async () => {
								const clipboardText = await navigator.clipboard.readText();
								if (canPaste(clipboardText, setting)) {
									setSetting(setting, key, JSON.parse(clipboardText).value);
								}
							}}
						>
							<Paste size="18" />
						</button>
						<Tooltip type="auto">{$t('config.paste')}</Tooltip>
					{/if}
					{#if canEditSetting(canEdit, key, setting)}
						{#if settings?.settings[key] !== undefined}
							<button class="ds-icon-btn" onclick={() => setSetting(setting, key, null)}>
								<X size="18" />
							</button>
							<Tooltip type="auto">{$t('config.clear')}</Tooltip>
						{:else if canEditSetting(canEdit, key, setting)}
							<button
								class="ds-icon-btn"
								onclick={() =>
									setSetting(
										setting,
										key,
										typeof setting.type === 'object' && setting.type.hasOwnProperty('list-of')
											? []
											: ''
									)}
							>
								<Pen size="18" />
							</button>
							<Tooltip type="auto">{$t('config.edit')}</Tooltip>
						{/if}
					{/if}
					{#if showRouting}
						{#if other && other.length > 0}
							{#if sameOrigin(settings, other[0])}
								{@const otherDefinitions = other.filter((o) => !sameOrigin(settings, o))}
								<button class="ds-icon-btn" onclick={() => {}}>
									<Route class="text-[var(--ds-accent-strong)]" size="18" />
								</button>
								<Tooltip type="auto" class="z-50">
									<P size="sm" class="whitespace-pre-line">{$t('config.passed')}</P>
									{#if otherDefinitions?.length > 0}
										<P size="sm" class="whitespace-pre-line mt-2">{$t('config.otherDefinitions')}</P
										>
										<div class="grid grid-cols-2 gap-x-4">
											{#each otherDefinitions as otherDefinition}
												<DefinitionLine origin={otherDefinition} value={otherDefinition.setting} />
											{/each}
										</div>
									{:else}
										<P size="sm" class="whitespace-pre-line mt-2"
											>{$t('config.noOtherDefinitions')}</P
										>
									{/if}
								</Tooltip>
							{:else}
								{@const otherDefinitions = other.filter(
									(o) => !sameOrigin(o, settings) && !sameOrigin(o, other[0])
								)}
								<button class="ds-icon-btn" onclick={() => {}}>
									<RouteOff class="text-[var(--ds-accent-strong)]" size="18" />
								</button>
								<Tooltip type="auto" class="z-50">
									<P size="sm" class="whitespace-pre-line">{@html $t('config.notPassed')}</P>
									<P size="sm" class="whitespace-pre-line mt-2">{$t('config.overwrittenBy')}</P>
									<div class="grid grid-cols-2 gap-x-4">
										<DefinitionLine origin={other[0]} value={other[0].setting} />
									</div>
									{#if otherDefinitions?.length > 0}
										<P size="sm" class="whitespace-pre-line mt-4">{$t('config.otherDefinitions')}</P
										>
										<div class="grid grid-cols-2 gap-x-4">
											{#each otherDefinitions as otherDefinition}
												<DefinitionLine origin={otherDefinition} value={otherDefinition.setting} />
											{/each}
										</div>
									{/if}
								</Tooltip>
							{/if}
						{:else if self !== undefined}
							<button class="ds-icon-btn" onclick={() => {}}>
								<Route class="text-[var(--ds-accent-strong)]" size="18" />
							</button>
							<Tooltip type="auto" class="z-50">
								<P size="sm" class="whitespace-pre-line">{@html $t('config.passed')}</P>
								<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
							</Tooltip>
						{:else}
							<button class="ds-icon-btn" onclick={() => {}}>
								<RouteOff class="text-[var(--ds-accent-strong)]" size="18" />
							</button>
							<Tooltip type="auto" class="z-50">
								<P size="sm" class="whitespace-pre-line">{@html $t('config.notSet')}</P>
								<P size="sm" class="whitespace-pre-line mt-2">{$t('config.noOtherDefinitions')}</P>
							</Tooltip>
						{/if}
					{/if}
				</div>
				{#if setting.description}
					<p class="ds-form-hint whitespace-pre-line">{setting.description}</p>
				{/if}
			</div>
		{:else}
			<div class="ds-table-empty">{$t('config.no-settings')}</div>
		{/each}
	</div>
</div>
