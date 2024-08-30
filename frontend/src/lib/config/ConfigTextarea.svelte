<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Textarea, Tooltip } from 'flowbite-svelte';
	export let placeholder: string | null;
	export let value: unknown;

	export let onChange: (value: string) => void = () => {};
	export let disabled: boolean;

	const changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};
</script>

<Textarea {placeholder} on:change={changeInternal} {value} {disabled} rows={16} />
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
