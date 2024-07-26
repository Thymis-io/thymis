<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Tooltip } from 'flowbite-svelte';
	export let placeholder: string | null;
	export let value: unknown;

	export let change: (value: string) => void = () => {};
	export let disabled: boolean;

	let changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).value);
	};
</script>

<Input type="text" {placeholder} value={value || ''} {disabled} on:change={changeInternal} />
{#if disabled}
	<Tooltip placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
