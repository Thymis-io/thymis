<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Helper, Input, Label, Modal, P, Select } from 'flowbite-svelte';
	import {
		type Device,
		type Module,
		saveState,
		type SelectOneSettingType,
		type SettingType,
		state
	} from '$lib/state';
	import { page } from '$app/stores';
	import { nameToIdentifier, nameValidation, deviceTypeValidation } from '$lib/nameValidation';
	import MultiSelect from 'svelte-multiselect';

	export let open = false;

	let displayName = '';

	$: availableModules = $page.data.availableModules as Module[];
	$: thymisDeviceModule = availableModules.find(
		(module) => module.type === 'thymis_controller.modules.thymis.ThymisDevice'
	);
	const isASelectOneSetting = (type: SettingType | undefined): type is SelectOneSettingType =>
		!!type && typeof type === 'object' && 'select-one' in type && Array.isArray(type['select-one']);
	$: deviceTypes = isASelectOneSetting(thymisDeviceModule?.settings['device_type'].type)
		? thymisDeviceModule?.settings['device_type'].type['select-one']
		: [];
	$: deviceTypesSelect = deviceTypes?.map((deviceType) => ({
		name: deviceType[0],
		value: deviceType[1]
	}));
	let selectedDeviceType: string | undefined = undefined;

	$: tags = $state.tags;
	$: tagsSelect = tags.map((tag) => ({ value: tag.identifier, label: tag.displayName }));
	let selectedTags: { value: string; label: string }[] = [];

	const submitData = async () => {
		if (
			nameValidation(displayName, 'device') ||
			deviceTypeValidation(selectedDeviceType) ||
			!thymisDeviceModule?.type ||
			!selectedDeviceType
		)
			return;
		const identifier = nameToIdentifier(displayName);
		const thymisDeviceModuleSettings = {
			device_type: selectedDeviceType,
			device_name: identifier,
			nix_state_version: '24.05',
			agent_controller_url: `${window.location.protocol}//${window.location.host}`,
			agent_enabled: true
		};
		const device: Device = {
			displayName,
			identifier,
			targetHost: '',
			tags: selectedTags.map((tag) => tag.value),
			modules: [{ type: thymisDeviceModule?.type, settings: thymisDeviceModuleSettings }]
		};
		$state.devices = [...$state.devices, device];
		await saveState();

		open = false;
	};
</script>

<Modal
	title={$t('create-device.title')}
	bind:open
	outsideclose
	size="lg"
	on:close={() => {
		displayName = '';
		selectedDeviceType = undefined;
		selectedTags = [];
	}}
	on:open={() => {
		setTimeout(() => {
			const displayNameHtmlInput = document.getElementById('display-name');
			displayNameHtmlInput?.focus();
		}, 1);
	}}
	bodyClass="p-4 md:p-5 space-y-4 flex-1"
>
	<form>
		<div class="mb-4">
			<Label for="display-name"
				>{$t('create-device.display-name')}
				<Input id="display-name" bind:value={displayName} />
				{#if nameValidation(displayName, 'device')}
					<Helper color="red">{nameValidation(displayName, 'device')}</Helper>
				{:else}
					<Helper color="green"
						>{$t('create-device.name-helper', {
							values: { identifier: nameToIdentifier(displayName) }
						})}</Helper
					>
				{/if}
			</Label>
		</div>
		<div class="mb-4">
			<Label for="device-type"
				>{$t('create-device.device-type')}
				<Select id="device-type" items={deviceTypesSelect} bind:value={selectedDeviceType} />
				{#if deviceTypeValidation(selectedDeviceType)}
					<Helper color="red">{deviceTypeValidation(selectedDeviceType)}</Helper>
				{/if}
			</Label>
		</div>
		<div class="mb-4">
			{#if tags.length > 0}
				<Label for="tags">
					{$t('create-device.tags')}
					<MultiSelect
						id="tags"
						options={tagsSelect}
						bind:selected={selectedTags}
						outerDivClass="w-full"
					/>
				</Label>
			{:else}
				<P>{$t('create-device.no-tags')}</P>
			{/if}
		</div>
		<div class="flex justify-end">
			<Button
				type="button"
				class="btn btn-primary"
				disabled={!!(
					nameValidation(displayName, 'device') || deviceTypeValidation(selectedDeviceType)
				)}
				on:click={submitData}
			>
				{$t('create-device.create')}
			</Button>
		</div>
	</form>
</Modal>
