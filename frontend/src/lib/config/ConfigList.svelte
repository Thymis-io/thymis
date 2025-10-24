<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip, Card, P } from 'flowbite-svelte';
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

<div class="flex flex-col gap-1 w-full">
	{#each values as item, i}
		<Card class="flex flex-row gap-1 p-4 w-full max-w-full drop-shadow" padding={'xs'}>
			<div class="flex flex-col w-full gap-4">
				{#each Object.entries(setting.type['list-of']) as [keyEntry, settingEntry]}
					<div>
						{#if settingEntry.displayName}
							<P id="{key}-{i}-{keyEntry}" class="p-0 pb-1">{$t(`${settingEntry.displayName}`)}</P>
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
				class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
				{disabled}
				onclick={() => onChange(values.filter((v) => v !== item))}
			>
				<X />
			</button>
			<Tooltip type="auto" placement={'top'}>
				{setting.type['element-name']
					? $t(`config.remove-element`, {
							values: { element: $t(setting.type['element-name']) }
						})
					: $t('config.remove_list_element')}
			</Tooltip>
		</Card>
	{/each}
	<Card class="flex flex-row gap-1 w-full max-w-full drop-shadow" padding={'xs'}>
		<button
			class="p-1 w-full flex justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700 gap-2"
			{disabled}
			onclick={() => onChange([...values, {}])}
		>
			<Plus size="20" />
			<span class="text-base">
				{setting.type['element-name']
					? $t(`config.add-element`, { values: { element: $t(setting.type['element-name']) } })
					: $t('config.add_list_element')}
			</span>
		</button>
	</Card>
</div>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
