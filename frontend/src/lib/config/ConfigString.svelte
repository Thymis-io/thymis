<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip } from 'flowbite-svelte';
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
	}: Props & HTMLInputAttributes = $props();

	let changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};

	const className =
		'block w-full disabled:cursor-not-allowed disabled:opacity-50 rtl:text-right p-2.5 ' +
		'focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-500 dark:focus:ring-primary-500 ' +
		'bg-gray-50 text-gray-900 dark:bg-gray-600 dark:text-white dark:placeholder-gray-400 border border-gray-300 dark:border-gray-500 ' +
		'text-sm rounded-lg px-2 py-1';
</script>

<input
	type="text"
	class={className}
	{placeholder}
	value={value || ''}
	{disabled}
	onchange={changeInternal}
	{...props}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
