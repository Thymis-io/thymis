<script lang="ts">
	import type {
		ListSettingType,
		ModuleSettings,
		SecretSettingType,
		SelectOneSettingType,
		Setting
	} from '$lib/state';
	import ConfigString from './ConfigString.svelte';
	import ConfigBool from './ConfigBool.svelte';
	import ConfigTextarea from './ConfigTextarea.svelte';
	import ConfigSelectOne from './ConfigSelectOne.svelte';
	import ConfigList from './ConfigList.svelte';
	import ConfigInt from './ConfigInt.svelte';
	import ConfigSecret from './ConfigSecret.svelte';

	export let setting: Setting;
	export let value: unknown;
	export let disabled: boolean;

	export let moduleSettings: ModuleSettings | undefined;

	export let onChange: (value: any) => void;

	const getTypeKeyFromSetting = (setting: Setting): string | undefined => {
		if (setting.type === 'int') return 'int';
		if (setting.type === 'bool') return 'bool';
		if (setting.type === 'string') return 'string';
		if (setting.type === 'textarea') return 'textarea';
		if (typeof setting.type === 'object' && setting.type.hasOwnProperty('select-one')) {
			return 'select-one';
		}
		if (typeof setting.type === 'object' && setting.type.hasOwnProperty('list-of')) {
			return 'list-of';
		}
		if (typeof setting.type === 'object' && setting.type.hasOwnProperty('inline-file')) {
			return 'inline-file';
		}
		if (
			typeof setting.type === 'object' &&
			setting.type.hasOwnProperty('type') &&
			setting.type.type === 'secret'
		) {
			return 'secret';
		}
		console.error(`Unknown setting type: ${setting.type}`);
	};

	const settingIsInt = (setting: Setting): setting is Setting<'int'> => {
		return getTypeKeyFromSetting(setting) === 'int';
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

	const settingIsListOf = (setting: Setting): setting is Setting<ListSettingType> => {
		return getTypeKeyFromSetting(setting) === 'list-of';
	};

	const settingIsSecret = (setting: Setting): setting is Setting<SecretSettingType> => {
		return getTypeKeyFromSetting(setting) === 'secret';
	};
</script>

{#if settingIsInt(setting)}
	<ConfigInt {value} placeholder={setting.example} {onChange} {disabled} />
{:else if settingIsBool(setting)}
	<ConfigBool value={value === true} name={setting.displayName} {onChange} {disabled} />
{:else if settingIsString(setting)}
	<ConfigString {value} placeholder={setting.example} {onChange} {disabled} />
{:else if settingIsTextarea(setting)}
	<ConfigTextarea {value} placeholder={setting.example} {onChange} {disabled} />
{:else if settingIsSelectOne(setting)}
	<ConfigSelectOne {value} {setting} {moduleSettings} {onChange} {disabled} />
{:else if settingIsListOf(setting)}
	<ConfigList
		values={Array.isArray(value) ? value : []}
		{setting}
		{moduleSettings}
		{onChange}
		{disabled}
	/>
{:else if settingIsSecret(setting)}
	<ConfigSecret {value} {setting} placeholder={setting.example} {onChange} {disabled} />
{/if}
