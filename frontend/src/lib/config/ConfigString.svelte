<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip } from 'flowbite-svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props {
		placeholder: string | null | undefined;
		value: unknown;
		onChange?: (value: string) => void;
		disabled: boolean;
		validate?: (value: unknown) => boolean;
		validationError?: string;
		props: HTMLInputAttributes;
	}

	let {
		placeholder,
		value,
		onChange = () => {},
		disabled,
		validate = () => true,
		validationError = '',
		...props
	}: Props & HTMLInputAttributes = $props();

	let edited = $state<string | null>(null);
	let lastValue = $state<unknown>(undefined);
	let initialized = false;

	let draft = $derived(edited ?? (typeof value === 'string' ? value : ''));
	let invalid = $derived(!validate(draft));

	$effect(() => {
		if (!initialized || value !== lastValue) {
			initialized = true;
			lastValue = value;
			edited = null;
		}
	});

	let inputInternal = (e: Event) => {
		edited = (e.target as HTMLInputElement).value;
	};

	let changeInternal = (e: Event) => {
		const newValue = (e.target as HTMLInputElement).value;
		if (validate(newValue)) {
			onChange(newValue);
		}
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
	class:invalid
	{placeholder}
	value={draft}
	{disabled}
	aria-invalid={invalid}
	oninput={inputInternal}
	onchange={changeInternal}
	{...props}
/>
{#if invalid && validationError}
	<p class="validation-error" role="alert">{validationError}</p>
{/if}
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}

<style>
	input.invalid {
		border-color: var(--ds-danger) !important;
	}

	input.invalid:focus {
		border-color: var(--ds-danger) !important;
		box-shadow: 0 0 0 3px var(--ds-danger-dim);
	}

	.validation-error {
		margin-top: 4px;
		color: var(--ds-danger);
		font-size: 11.5px;
	}
</style>
