<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Select, Tooltip } from 'flowbite-svelte';
	import type { ModuleSettings, SelectOneSettingType, Setting } from '$lib/state';
	import { browser } from '$app/environment';

	export let value: string = '';
	export let setting: Setting<SelectOneSettingType>;

	export let moduleSettings: ModuleSettings | undefined;

	export let onChange: (value: string) => void = () => {};
	export let disabled: boolean = false;

	const changeInternal = (e: Event) => {
		onChange((e.target as HTMLInputElement).value);
	};

	// if setting has .extra_data:

	$: extraData = setting.type.extra_data;

	let available_settings = setting.type['select-one'];

	$: {
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
			// if current value is not in available settings, set it to the first available
			if (!available_settings.map((option) => option[1]).includes(value)) {
				value = available_settings?.[0]?.[1];
				if (browser) onChange(value);
			}
		} else {
			available_settings = setting.type['select-one'];
		}
	}
</script>

<Select
	{value}
	on:change={changeInternal}
	items={available_settings?.map((option) => ({
		name: option[0],
		value: option[1]
	}))}
	{disabled}
	class={disabled ? 'opacity-70' : ''}
/>
{#if disabled}
	<Tooltip type="auto" placement={'top'}>{$t('config.editDisabled')}</Tooltip>
{/if}
