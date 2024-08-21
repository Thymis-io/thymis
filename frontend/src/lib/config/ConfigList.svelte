<script lang="ts">
	import { t } from 'svelte-i18n';
	import { List, Tooltip } from 'flowbite-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import type { Setting, ListSettingType } from '$lib/state';
	import ConfigDrawer from './ConfigDrawer.svelte';

	export let values: any[];
	export let settings: Setting<ListSettingType>;
	export let onChange: (value: unknown[]) => void = () => {};
	export let disabled: boolean = false;

	$: console.log('values', values, settings.type['list-of']);
</script>

<div>
	<div class="flex flex-col gap-1">
		{#each values as item}
			{#each Object.entries(settings.type['list-of']) as [key, setting]}
				<ConfigDrawer
					{setting}
					value={item[key]}
					{disabled}
					onChange={(value) => {
						const newValues = [...values];
						newValues[values.indexOf(item)] = { ...item, [key]: value };
						onChange(newValues);
					}}
				/>
			{/each}
		{/each}
	</div>
	<button
		class="p-2 w-full flex justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700"
		on:click={() => onChange([...values, {}])}
	>
		<Plus />
	</button>
	<Tooltip type="auto" placement={'top'}>{$t('config.add_list_item')}</Tooltip>
</div>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
