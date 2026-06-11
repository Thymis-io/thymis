<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip } from 'flowbite-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import X from 'lucide-svelte/icons/x';
	import type { Setting, ListSettingType, ModuleSettings } from '$lib/state';
	import ConfigRenderer from './ConfigRenderer.svelte';
	import type { Artifact } from '../../routes/(authenticated)/artifacts/[...rest]/+page';

	interface Props {
		key: string;
		values: any[];
		setting: Setting<ListSettingType>;
		moduleSettings: ModuleSettings | undefined;
		onChange?: (value: unknown[]) => void;
		disabled?: boolean;
		artifacts: Artifact[];
	}

	let {
		key,
		values,
		setting,
		moduleSettings,
		onChange = () => {},
		disabled = false,
		artifacts
	}: Props = $props();
</script>

<div class="flex w-full flex-col gap-2">
	{#each values as item, i}
		<div
			class="flex w-full max-w-full flex-row gap-2 rounded-lg border border-[var(--ds-border)] bg-[var(--ds-surface-2)] p-4"
		>
			<div class="flex w-full flex-col gap-4">
				{#each Object.entries(setting.type['list-of']) as [keyEntry, settingEntry]}
					<div class="flex flex-col gap-2">
						{#if settingEntry.displayName}
							<span id="{key}-{i}-{keyEntry}" class="ds-form-label"
								>{$t(`${settingEntry.displayName}`)}</span
							>
						{/if}
						<ConfigRenderer
							key="{key}-{i}-{keyEntry}"
							setting={settingEntry}
							{moduleSettings}
							value={item[keyEntry]}
							{disabled}
							onChange={(value) => {
								const newValues = [...values];
								newValues[values.indexOf(item)] = { ...item, [keyEntry]: value };
								onChange(newValues);
							}}
							{artifacts}
						/>
					</div>
				{/each}
			</div>
			<button
				class="m-0 h-min rounded-lg p-1 text-[var(--ds-text-mute)] hover:bg-[var(--ds-surface-3)] hover:text-[var(--ds-text)] disabled:cursor-not-allowed disabled:opacity-50"
				{disabled}
				onclick={() => onChange(values.filter((v) => v !== item))}
			>
				<X size="20" />
			</button>
			<Tooltip type="auto" placement={'top'}>
				{setting.type['element-name']
					? $t(`config.remove-element`, {
							values: { element: $t(setting.type['element-name']) }
						})
					: $t('config.remove_list_element')}
			</Tooltip>
		</div>
	{/each}
	<button
		class="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--ds-border-strong)] p-2 text-sm font-medium text-[var(--ds-text-dim)] transition-colors hover:border-[var(--ds-accent)] hover:bg-[var(--ds-accent-dim)] hover:text-[var(--ds-accent-strong)] disabled:cursor-not-allowed disabled:opacity-50"
		{disabled}
		onclick={() => onChange([...values, {}])}
	>
		<Plus size="18" />
		<span>
			{setting.type['element-name']
				? $t(`config.add-element`, { values: { element: $t(setting.type['element-name']) } })
				: $t('config.add_list_element')}
		</span>
	</button>
</div>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
