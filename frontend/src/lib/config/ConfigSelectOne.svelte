<script lang="ts">
	import { run } from 'svelte/legacy';

	import { t } from 'svelte-i18n';
	import { Select, Tooltip } from 'flowbite-svelte';
	import type { ModuleSettings, SelectOneSettingType, Setting } from '$lib/state';
	import { browser } from '$app/environment';

	interface Props {
		value?: string;
		setting: Setting<SelectOneSettingType>;
		moduleSettings: ModuleSettings | undefined;
		onChange?: (value: string) => void;
		disabled?: boolean;
	}

	let {
		value = $bindable(''),
		setting,
		moduleSettings,
		onChange = () => {},
		disabled = false
	}: Props = $props();

	const changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};

	// if setting has .extra_data:

	let extraData = $derived(setting.type.extra_data);

	let available_settings = $state(setting.type['select-one']);
	let last_available_settings = $state(JSON.stringify(available_settings));

	run(() => {
		if (extraData && 'restrict_values_on_other_key' in extraData) {
			let available_settings_set = new Set<string>(
				setting.type['select-one'].map((option) => option[1])
			);
			if (typeof extraData['restrict_values_on_other_key'] === 'object') {
				for (const otherKey in extraData['restrict_values_on_other_key']) {
					if (!moduleSettings?.settings || !(otherKey in moduleSettings?.settings)) {
						continue;
					}
					const otherValue = moduleSettings?.settings[otherKey];
					if (!otherValue || !(typeof otherValue === 'string')) {
						continue;
					}
					const restrictValues =
						extraData['restrict_values_on_other_key'][otherKey][otherValue] || [];
					available_settings_set = available_settings_set.intersection(new Set(restrictValues));
				}
			}
			available_settings = setting.type['select-one'].filter((option) =>
				available_settings_set.has(option[1])
			);
			// if current value is not in available settings, set it to the first available, only if available_settings just changed
			if (
				!available_settings.map((option) => option[1]).includes(value) &&
				JSON.stringify(available_settings) !== last_available_settings
			) {
				value = available_settings?.[0]?.[1];
				if (browser) onChange(value);
			}
			last_available_settings = JSON.stringify(available_settings);
		} else {
			available_settings = setting.type['select-one'];
		}
	});
</script>

<Select
	{value}
	on:change={changeInternal}
	items={available_settings?.map((option) => ({
		name: option[0],
		value: option[1]
	}))}
	{disabled}
	class={`h-8 px-2 py-1 ${disabled ? 'opacity-70' : ''}`}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
