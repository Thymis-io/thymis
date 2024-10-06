<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Select, Tooltip } from 'flowbite-svelte';
	import type { ModuleSettings, SelectOneSettingType, Setting } from '$lib/state';

	export let value: unknown = '';
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
		if (extraData && 'thymis_controller.modules.thymis.ThymisDevice' in extraData) {
			if (typeof extraData['thymis_controller.modules.thymis.ThymisDevice'] === 'string') {
			} else if (typeof extraData['thymis_controller.modules.thymis.ThymisDevice'] === 'object') {
				const device_type =
					moduleSettings && 'device_type' in moduleSettings?.settings
						? moduleSettings?.settings['device_type']
						: undefined;
				if (!device_type || typeof device_type !== 'string') {
					console.error('device_type not found in moduleSettings');
				} else {
					const available_formats_for_device =
						extraData['thymis_controller.modules.thymis.ThymisDevice'][
							'available_formats_for_device'
						][device_type];
					if (available_formats_for_device) {
						available_settings = setting.type['select-one'].filter((option) =>
							available_formats_for_device.includes(option[1])
						);
					} else {
						console.error('available_formats_for_device not found in extra_data');
					}
				}
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
