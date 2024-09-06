<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip, Card, P } from 'flowbite-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import X from 'lucide-svelte/icons/x';
	import type { Setting, ListSettingType } from '$lib/state';
	import ConfigRenderer from './ConfigRenderer.svelte';

	export let values: any[];
	export let settings: Setting<ListSettingType>;
	export let onChange: (value: unknown[]) => void = () => {};
	export let disabled: boolean = false;
</script>

<div class="flex flex-col gap-1 w-full">
	{#each values as item}
		<Card class="flex flex-row gap-1 p-4 w-full max-w-full drop-shadow" padding={'xs'}>
			<div class="flex flex-col w-full gap-4">
				{#each Object.entries(settings.type['list-of']) as [key, setting]}
					<div>
						{#if setting.name}
							<P class="p-0 pb-1">{$t(`options.nix.${setting.name}`, { default: setting.name })}</P>
						{/if}
						<ConfigRenderer
							{setting}
							value={item[key]}
							{disabled}
							onChange={(value) => {
								const newValues = [...values];
								newValues[values.indexOf(item)] = { ...item, [key]: value };
								onChange(newValues);
							}}
						/>
					</div>
				{/each}
			</div>
			<button
				class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
				{disabled}
				on:click={() => onChange(values.filter((v) => v !== item))}
			>
				<X />
			</button>
			<Tooltip type="auto" placement={'top'}>
				{settings.type['element-name']
					? $t(`options.nix.remove-element`, {
							values: { element: $t(settings.type['element-name']) }
						})
					: $t('config.remove_list_element')}
			</Tooltip>
		</Card>
	{/each}
	<Card class="flex flex-row gap-1 w-full max-w-full drop-shadow" padding={'xs'}>
		<button
			class="p-2 w-full flex justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700 gap-2"
			{disabled}
			on:click={() => onChange([...values, {}])}
		>
			<Plus />
			{settings.type['element-name']
				? $t(`options.nix.add-element`, { values: { element: $t(settings.type['element-name']) } })
				: $t('config.add_list_element')}
		</button>
	</Card>
</div>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
