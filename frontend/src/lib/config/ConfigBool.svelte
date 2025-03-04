<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Toggle, Tooltip } from 'flowbite-svelte';
	interface Props {
		name: string;
		value?: boolean | undefined;
		onChange?: (value: boolean) => void;
		disabled: boolean;
	}

	let { name, value = false, onChange = () => {}, disabled }: Props = $props();

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
