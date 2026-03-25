<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Helper, Input, Label, Modal, P, Select } from 'flowbite-svelte';
	import { type Config, type Module, saveState } from '$lib/state';
	import { page } from '$app/stores';
	import { nameToIdentifier, nameValidation, deviceTypeValidation } from '$lib/nameValidation';
	import MultiSelect from 'svelte-multiselect';
	import {
		getThymisDeviceModule,
		getDeviceTypesMap,
		getAllowedImageFormatsForDeviceType
	} from '$lib/config/configUtils';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		open?: boolean;
	}

	let { globalState, open = $bindable(false) }: Props = $props();

	let displayName = $state('');

	let availableModules = $derived($page.data.availableModules as Module[]);
	let thymisDeviceModule = $derived(getThymisDeviceModule(availableModules));
	let deviceTypesSelect = $derived(
		Object.entries(getDeviceTypesMap(availableModules)).map(([key, name]) => ({
			name: name,
			value: key
		}))
	);
	let selectedDeviceType: string | undefined = $state(undefined);

	let tags = $derived(globalState.tags);
	let tagsSelect = $derived(tags.map((tag) => ({ value: tag.identifier, label: tag.displayName })));
	let selectedTags: { value: string; label: string }[] = $state([]);

	const submitData = async () => {
		if (
			nameValidation(globalState, displayName, 'config') ||
			deviceTypeValidation(selectedDeviceType) ||
			!thymisDeviceModule?.type ||
			!selectedDeviceType
		) {
			console.error('Invalid data when creating device');
			return;
		}
		const identifier = nameToIdentifier(displayName);
		const thymisDeviceModuleSettings = {
			device_type: selectedDeviceType,
			image_format:
				getAllowedImageFormatsForDeviceType(selectedDeviceType, availableModules)?.[0] ||
				'sd-card-image',
			device_name: identifier,
			nix_state_version: '25.11'
		};
		const config: Config = {
			displayName,
			identifier,
			tags: selectedTags.map((tag) => tag.value),
			modules: [{ type: thymisDeviceModule?.type, settings: thymisDeviceModuleSettings }]
		};
		globalState.configs = [...globalState.configs, config];
		await saveState(globalState);

		open = false;
	};
</script>

<Modal
	title={$t('create-configuration.title')}
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
				>{$t('create-configuration.display-name')}
				<Input id="display-name" bind:value={displayName} />
				{#if nameValidation(globalState, displayName, 'config')}
					<Helper color="red">{nameValidation(globalState, displayName, 'config')}</Helper>
				{:else}
					<Helper color="green"
						>{$t('create-configuration.name-helper', {
							values: { identifier: nameToIdentifier(displayName) }
						})}</Helper
					>
				{/if}
			</Label>
		</div>
		<div class="mb-4">
			<Label for="device-type"
				>{$t('create-configuration.device-type')}
				<Select id="device-type" items={deviceTypesSelect} bind:value={selectedDeviceType} />
				{#if deviceTypeValidation(selectedDeviceType)}
					<Helper color="red">{deviceTypeValidation(selectedDeviceType)}</Helper>
				{/if}
			</Label>
		</div>
		<div class="mb-4">
			{#if tags.length > 0}
				<Label for="tags">
					{$t('create-configuration.tags')}
					<MultiSelect
						id="tags"
						options={tagsSelect}
						bind:selected={selectedTags}
						outerDivClass="w-full"
					/>
				</Label>
			{:else}
				<P>{$t('create-configuration.no-tags')}</P>
			{/if}
		</div>
		<div class="flex justify-end">
			<Button
				type="button"
				class="btn btn-primary"
				disabled={!!(
					nameValidation(globalState, displayName, 'config') ||
					deviceTypeValidation(selectedDeviceType)
				)}
				on:click={submitData}
			>
				{$t('create-configuration.create')}
			</Button>
		</div>
	</form>
</Modal>
