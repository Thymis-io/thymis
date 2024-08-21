<script lang="ts">
	import type { Module, ModuleSettings, SelectOneSettingType, Setting } from '$lib/state';
	import ConfigString from './ConfigString.svelte';
	import ConfigBool from './ConfigBool.svelte';
	import ConfigTextarea from './ConfigTextarea.svelte';
	import ConfigSelectOne from './ConfigSelectOne.svelte';

	export let setting: Setting;
	export let value: unknown;
	export let disabled: boolean;

	export let onChange: (value: any) => void;

	const getTypeKeyFromSetting = (setting: Setting): string => {
		if (setting.type === 'bool') return 'bool';
		if (setting.type === 'string') return 'string';
		if (setting.type === 'textarea') return 'textarea';
		if (typeof setting.type === 'object' && setting.type.hasOwnProperty('select-one')) {
			return 'select-one';
		}
		if (typeof setting.type === 'object' && setting.type.hasOwnProperty('list-of')) {
			return 'list-of';
		}
		throw new Error(`Unknown setting type: ${setting.type}`);
	};

	const settingIsBool = (setting: Setting): setting is Setting<'bool'> => {
		return getTypeKeyFromSetting(setting) === 'bool';
	};

	const settingIsString = (setting: Setting): setting is Setting<'string'> => {
		return getTypeKeyFromSetting(setting) === 'string';
	};

	const settingIsTextarea = (setting: Setting): setting is Setting<'textarea'> => {
		return getTypeKeyFromSetting(setting) === 'textarea';
	};

	const settingIsSelectOne = (setting: Setting): setting is Setting<SelectOneSettingType> => {
		return getTypeKeyFromSetting(setting) === 'select-one';
	};
</script>

{#if settingIsBool(setting)}
	<ConfigBool value={value === true} name={setting.name} {onChange} {disabled} />
{:else if settingIsString(setting)}
	<ConfigString {value} placeholder={setting.default} {onChange} {disabled} />
{:else if settingIsTextarea(setting)}
	<ConfigTextarea {value} placeholder={setting.default} {onChange} {disabled} />
{:else if settingIsSelectOne(setting)}
	<ConfigSelectOne {value} {setting} {onChange} {disabled} />
{/if}
