<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Select, Tooltip } from 'flowbite-svelte';
	import type { SelectOneSettingType, Setting } from '$lib/state';

	export let value: unknown = '';
	export let setting: Setting<SelectOneSettingType>;
	export let onChange: (value: string) => void = () => {};
	export let disabled: boolean = false;

	const changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};
</script>

<Select
	{value}
	on:change={changeInternal}
	items={setting.type['select-one']?.map((option) => ({
		name: option[0],
		value: option[1]
	}))}
	{disabled}
	class={disabled ? 'opacity-70' : ''}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
