<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Toggle, Tooltip } from 'flowbite-svelte';
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props {
		name: string;
		value?: boolean | undefined;
		onChange?: (value: boolean) => void;
		disabled: boolean;
	}

	let {
		name,
		value = false,
		onChange = () => {},
		disabled,
		...props
	}: Props & Omit<HTMLInputAttributes, 'required' | 'class' | 'color' | 'size'> = $props();

	let changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).checked);
	};
</script>

<Toggle
	class="h-6"
	size="small"
	{name}
	checked={value}
	on:change={changeInternal}
	{disabled}
	{...props}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top-start'}>{$t('config.editDisabled')}</Tooltip>
{/if}
