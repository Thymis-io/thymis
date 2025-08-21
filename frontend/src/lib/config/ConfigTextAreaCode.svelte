<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Tooltip } from 'flowbite-svelte';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import type { TextAreaCodeSettingType } from '$lib/state';
	// import MonacoTextarea from '$lib/components/MonacoTextarea.svelte';

	interface Props {
		placeholder: string | null;
		value: unknown;
		onChange?: (value: string) => void;
		disabled: boolean;
		setting: TextAreaCodeSettingType;
	}

	let { placeholder, value, onChange = () => {}, disabled, setting }: Props = $props();
	let MonacoTextarea: typeof import('$lib/components/MonacoTextarea.svelte').default = $state();
	onMount(async () => {
		MonacoTextarea = (await import('$lib/components/MonacoTextarea.svelte')).default;
	});
</script>

{#if browser}
	<MonacoTextarea {placeholder} {onChange} {value} {disabled} languages={setting.language} />
{/if}
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
