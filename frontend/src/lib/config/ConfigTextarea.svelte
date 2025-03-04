<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Textarea, Tooltip } from 'flowbite-svelte';

	interface Props {
		placeholder: string | null;
		value: unknown;
		onChange?: (value: string) => void;
		disabled: boolean;
	}

	let { placeholder, value, onChange = () => {}, disabled }: Props = $props();

	const changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};
</script>

<Textarea {placeholder} on:change={changeInternal} {value} {disabled} rows={16} />
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
