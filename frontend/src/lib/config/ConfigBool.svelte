<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Toggle, Tooltip } from 'flowbite-svelte';
	export let name: string;
	export let value: boolean | undefined = false;
	export let onChange: (value: boolean) => void = () => {};
	export let disabled: boolean;

	let changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).checked);
	};
</script>

<Toggle
	class="mt-1.5 h-8"
	size="small"
	{name}
	checked={value}
	on:change={changeInternal}
	{disabled}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top-start'}>{$t('config.editDisabled')}</Tooltip>
{/if}
