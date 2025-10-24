<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Tooltip } from 'flowbite-svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props {
		placeholder: string | null;
		value: unknown;
		onChange?: (value: string) => void;
		disabled: boolean;
		props: HTMLInputAttributes;
	}

	let {
		placeholder,
		value,
		onChange = () => {},
		disabled,
		...props
	}: Props & Omit<HTMLInputAttributes, 'type' | 'size' | 'color'> = $props();

	let changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};
</script>

<Input
	type="number"
	class="px-2 py-1"
	{placeholder}
	value={value || ''}
	{disabled}
	on:change={changeInternal}
	{...props}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
