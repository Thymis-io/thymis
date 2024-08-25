<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip, Card, P } from 'flowbite-svelte';
	import Plus from 'lucide-svelte/icons/plus';
	import X from 'lucide-svelte/icons/x';
	import type { Setting, ListSettingType } from '$lib/state';
	import ConfigDrawer from './ConfigDrawer.svelte';

	export let values: any[];
	export let settings: Setting<ListSettingType>;
	export let onChange: (value: unknown[]) => void = () => {};
	export let disabled: boolean = false;

	$: console.log('values', values, settings.type['list-of']);
</script>

<div class="flex flex-col gap-1 w-full">
	{#each values as item}
		<Card class="flex flex-row gap-1 w-full max-w-full drop-shadow" padding={'xs'}>
			<div class="flex flex-col w-full">
				{#each Object.entries(settings.type['list-of']) as [key, setting]}
					<P class="p-2 pb-1">{$t(`options.nix.${setting.name}`, { default: setting.name })}</P>
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
			</div>
			<button
				class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
				on:click={() => onChange(values.filter((v) => v !== item))}
			>
				<X />
			</button>
			<Tooltip type="auto"><P size="sm">{$t('config.remove_list_item')}</P></Tooltip>
		</Card>
	{/each}
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
