<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Tooltip } from 'flowbite-svelte';

	interface Props {
		placeholder: string | null;
		value: unknown;
		onChange?: (value: string) => void;
		disabled: boolean;
	}

	let { placeholder, value, onChange = () => {}, disabled }: Props = $props();

	let changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};
</script>

<Input
	type="text"
	class="px-2 py-1"
	{placeholder}
	value={value || ''}
	{disabled}
	on:change={changeInternal}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
