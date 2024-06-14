<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Select, Tooltip } from 'flowbite-svelte';
	import type { Setting } from '$lib/state';

	export let value: unknown = '';
	export let options: string[] = [];
	export let setting: Setting;
	export let change: (value: string) => void = () => {};
	export let disabled: boolean;

	const changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).value);
	};
</script>

<Select
	{value}
	on:change={changeInternal}
	items={options.map((option) => ({
		value: option,
		name: $t(`options.nix.${setting.name}-options.${option}`)
	}))}
	{disabled}
/>
{#if disabled}
	<Tooltip placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
