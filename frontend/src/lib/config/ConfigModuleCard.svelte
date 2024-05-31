<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Module, ModuleSettings } from '$lib/state';
	import { Card, P } from 'flowbite-svelte';
	import ConfigString from './ConfigString.svelte';
	import ConfigBool from './ConfigBool.svelte';
	import ConfigTextarea from './ConfigTextarea.svelte';
	import ConfigSelectOne from './ConfigSelectOne.svelte';

	export let module: Module;
	export let settings: (ModuleSettings & { origin: string | undefined }) | undefined;
	export let otherSettings:
		| (ModuleSettings & { origin: string | undefined; priority: number })[]
		| undefined;

	export let setSetting: (module: ModuleSettings | Module, settingKey: string, value: any) => void;
</script>

<Card class="max-w-none grid grid-cols-4 gap-8">
	{#each Object.entries(module.settings) as [key, setting]}
		<P class="col-span-1">
			{$t(`options.nix.${setting.name}`, { default: setting.name })}
		</P>
		<div class="col-span-1">
			{#if setting.type == 'bool'}
				<ConfigBool
					value={settings?.settings[key] === true}
					name={setting.name}
					change={(value) => {
						setSetting(module, key, value);
					}}
				/>
			{:else if setting.type == 'string'}
				<ConfigString
					value={settings?.settings[key]}
					placeholder={setting.default}
					change={(value) => {
						setSetting(module, key, value);
					}}
				/>
			{:else if setting.type == 'textarea'}
				<ConfigTextarea
					value={settings?.settings[key]}
					placeholder={setting.default}
					change={(value) => {
						setSetting(module, key, value);
					}}
				/>
			{:else if setting.type == 'select-one'}
				<ConfigSelectOne
					value={settings?.settings[key]}
					options={setting.options}
					{setting}
					change={(value) => {
						setSetting(module, key, value);
					}}
				/>
			{/if}
		</div>
		<P class="col-span-2">{setting.description}</P>
	{:else}
		<div class="col-span-1">{$t('options.no-settings')}</div>
	{/each}
</Card>
