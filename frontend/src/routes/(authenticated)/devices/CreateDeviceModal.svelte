<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Helper, Input, Label, Modal, MultiSelect, P, Select } from 'flowbite-svelte';
	import { type Device, type Module, saveState, state } from '$lib/state';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	export let open = false;

	let displayName = '';
	const nameToIdentifier = (displayName: string): string =>
		// displayName.toLowerCase().replace(/[^a-z0-9]/g, '-');
		{
			// strip string first
			let identifier = displayName.toLowerCase().replace(/[^a-z0-9]/g, '-');
			// remove leading and trailing hyphens
			identifier = identifier.replace(/^-+|-+$/g, '');
			// remove multiple hyphens
			identifier = identifier.replace(/-+/g, '-');
			// prepend with 'device-' if it doesn't start with a letter
			identifier = /^[a-z]/.test(identifier) ? identifier : `device-${identifier}`;
			return identifier;
		};
	const nameValidation = (displayName: string): string | undefined => {
		if (displayName.length === 0) return $t('create-device.display-name-cannot-be-empty');
		if ($state.devices.find((device) => device.displayName === displayName))
			return $t('create-device.device-with-display-name-name-exists', { values: { displayName } });
		const identifier = nameToIdentifier(displayName);
		if ($state.devices.find((device) => device.identifier === identifier))
			return $t('create-device.identifier-exists');
	};

	$: availableModules = $page.data.availableModules as Module[];
	$: thymisDeviceModule = availableModules.find(
		(module) => module.type === 'thymis_controller.modules.thymis.ThymisDevice'
	);
	$: deviceTypes = thymisDeviceModule?.settings['device_type']?.options;
	$: deviceTypesSelect = deviceTypes?.map((deviceType) => ({
		value: deviceType,
		name: $t(`options.nix.thymis.config.device-type-options.${deviceType}`)
	}));
	let selectedDeviceType: string | undefined = undefined;
	const deviceTypeValidation = (deviceType: string | undefined): string | undefined => {
		if (!deviceType) return $t('create-device.device-type-cannot-be-empty');
	};

	$: tags = $state.tags;
	$: tagsSelect = tags.map((tag) => ({ value: tag.identifier, name: tag.displayName }));
	let selectedTags: string[] = [];

	const submitData = async () => {
		if (
			nameValidation(displayName) ||
			deviceTypeValidation(selectedDeviceType) ||
			!thymisDeviceModule?.type ||
			!selectedDeviceType
		)
			return;
		const identifier = nameToIdentifier(displayName);
		const thymisDeviceModuleSettings = {
			device_type: selectedDeviceType
		};
		const device: Device = {
			displayName,
			identifier,
			targetHost: '',
			tags: selectedTags,
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
>
	<form>
		<div class="mb-4">
			<Label for="display-name"
				>{$t('create-device.display-name')}
				<Input id="display-name" bind:value={displayName} />
				{#if nameValidation(displayName)}
					<Helper color="red">{nameValidation(displayName)}</Helper>
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
					<MultiSelect id="tags" items={tagsSelect} bind:value={selectedTags} />
				</Label>
			{:else}
				<P>{$t('create-device.no-tags')}</P>
			{/if}
		</div>
		<div class="flex justify-end">
			<Button
				type="button"
				class="btn btn-primary"
				disabled={!!(nameValidation(displayName) || deviceTypeValidation(selectedDeviceType))}
				on:click={submitData}
			>
				{$t('create-device.create')}
			</Button>
		</div>
	</form>
</Modal>
