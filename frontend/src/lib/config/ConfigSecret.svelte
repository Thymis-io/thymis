<script lang="ts">
	import { run } from 'svelte/legacy';

	import { t } from 'svelte-i18n';
	import { Button, Select } from 'flowbite-svelte';
	import { invalidate } from '$app/navigation';
	import SecretEditModal from '$lib/components/secrets/SecretEditModal.svelte';
	import type { SecretProcessingType, SecretSettingType, SecretType } from '$lib/state';
	import { page } from '$app/stores';
	import {
		type SecretEditState,
		stringToEnvVars,
		createSecretRequest,
		downloadSecretFile,
		resetFileInputById
	} from '$lib/components/secrets/secretUtils';
	import { onMount } from 'svelte';

	interface Props {
		value?: string | null;
		placeholder?: string | undefined;
		disabled?: boolean;
		setting: Setting<SecretSettingType>;
		onChange?: (value: string | null) => void;
	}

	let {
		value = $bindable(null),
		placeholder = undefined,
		disabled = false,
		setting,
		onChange = () => {}
	}: Props = $props();

	let allowedTypes: SecretType[] = $state(['single_line', 'multi_line', 'env_list', 'file']);
	run(() => {
		allowedTypes = setting['type']['allowed-types'] || allowedTypes;
	});

	// Secret selection/display
	let secretName: string = $state('');
	let showEditModal = $state(false);
	let isCreating = $state(false);

	// Secret editing states
	let editedSecretName = $state('');
	let editedSecretType: SecretType = $state('single_line');
	let editedSingleLineValue: string | null = $state(null);
	let editedMultiLineValue: string | undefined = $state(undefined);
	let editedFileValue: File | null = $state(null);
	let editedEnvVarList: [string, string][] | null = $state(null);
	let editedFileInfo = $state({ name: '', size: 0 });
	let includeInImage = $state(false);
	let editedProcessingType: SecretProcessingType = $state('none');
	let isLoadingFile = $state(false);

	// Access secrets from $page.data
	let secrets = $derived($page.data?.secrets || {});
	let secret = $derived((value && secrets[value]) || null);
	run(() => {
		editedSecretType = secret?.type || 'single_line';
	});
	run(() => {
		includeInImage =
			secret && secret.include_in_image !== undefined
				? secret.include_in_image
				: setting.type['default-save-to-image'] || false;
	});
	run(() => {
		editedProcessingType =
			secret?.processing_type || setting.type['default-processing-type'] || 'none';
	});

	// Filter secrets based on allowed types
	let filteredSecrets = $derived(
		Object.entries(secrets)
			.filter(([_, secret]) => allowedTypes.includes(secret.type))
			.sort((a, b) => a[1].display_name.localeCompare(b[1].display_name))
	);

	// Initialize with first allowed type
	run(() => {
		if (allowedTypes && allowedTypes.length > 0 && !allowedTypes.includes(editedSecretType)) {
			editedSecretType = allowedTypes[0] as SecretType;
		}
	});

	// Update secretName when value changes or on page load
	run(() => {
		if (value && secrets && secrets[value]) {
			secretName = secrets[value].display_name;
		} else {
			secretName = '';
		}
	});

	const openCreateModal = (): void => {
		resetEditState();
		isCreating = true;
		showEditModal = true;
	};

	const openEditModal = (): void => {
		if (value && secrets && secrets[value]) {
			const secret = secrets[value];
			initializeEditState(secret);
			isCreating = false;
			showEditModal = true;
		}
	};

	const initializeEditState = (secret: any): void => {
		editedSecretName = secret.display_name;
		editedSecretType = secret.type;

		// If the current secret type is not in allowed types, use the first allowed type
		if (!allowedTypes.includes(editedSecretType)) {
			editedSecretType = allowedTypes[0] as SecretType;
		}

		// Pre-select include in image and processing type from the existing secret
		includeInImage = secret.include_in_image;
		editedProcessingType = secret.processing_type;

		if (secret.type === 'single_line') {
			editedSingleLineValue = secret.value_str || '';
			editedMultiLineValue = undefined;
			editedFileValue = null;
			editedEnvVarList = null;
		} else if (secret.type === 'multi_line') {
			editedSingleLineValue = null;
			editedMultiLineValue = secret.value_str || '';
			editedFileValue = null;
			editedEnvVarList = null;
		} else if (secret.type === 'env_list') {
			editedSingleLineValue = null;
			editedMultiLineValue = undefined;
			editedFileValue = null;
			editedEnvVarList = stringToEnvVars(secret.value_str || '');
		} else if (secret.type === 'file') {
			editedSingleLineValue = null;
			editedMultiLineValue = undefined;
			editedFileInfo = {
				name: secret.filename || '',
				size: secret.value_size
			};
			editedFileValue = null;
			editedEnvVarList = null;
		}
	};

	const resetEditState = (): void => {
		editedSecretName = '';
		// Use first allowed type as default
		editedSecretType = allowedTypes[0] as SecretType;
		editedSingleLineValue = '';
		editedMultiLineValue = undefined;
		editedFileValue = null;
		editedFileInfo = { name: '', size: 0 };
		editedEnvVarList = [['', '']];

		// Pre-select from settings if available
		includeInImage = setting.type['default-save-to-image'] === true;
		editedProcessingType = setting.type['default-processing-type'] || 'none';
	};

	function handleFileChange(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			editedFileValue = input.files[0];
			editedFileInfo = {
				name: input.files[0].name,
				size: input.files[0].size
			};
		}
	}

	function addEnvVariable() {
		editedEnvVarList = [...(editedEnvVarList || [['', '']]), ['', '']];
	}

	function removeEnvVariable(index: number) {
		if (editedEnvVarList && editedEnvVarList.length > 1) {
			const newList = [...editedEnvVarList];
			newList.splice(index, 1);
			editedEnvVarList = newList;
		} else {
			editedEnvVarList = [['', '']];
		}
	}

	// Handle the saved event from the modal
	function handleSaved(event: CustomEvent<{ id: string; display_name: string }>) {
		value = event.detail.id;
		secretName = event.detail.display_name;
		onChange(event.detail.id);
		invalidate('/api/secrets');
		showEditModal = false;
	}

	// Handle error from modal
	function handleError(event: CustomEvent<string>) {
		alert($t('secrets.save-error') + (event.detail ? `: ${event.detail}` : ''));
	}

	const downloadFile = async (): Promise<void> => {
		if (!value || !editedFileInfo.name) return;

		isLoadingFile = true;
		try {
			await downloadSecretFile(value, editedFileInfo.name);
		} catch (error) {
			console.error('Error downloading file:', error);
			alert($t('secrets.download-error'));
		} finally {
			isLoadingFile = false;
		}
	};

	onMount(() => {
		if (value && secrets && secrets[value]) {
			secretName = secrets[value].display_name;
		}
	});

	const internalChange = async (event: Event) => {
		const select = event.target as HTMLSelectElement;
		value = select.value;
		onChange(value);
	};

	let selectItems = $state([]);
	run(() => {
		selectItems = filteredSecrets.map(([id, secret]) => ({
			name: `${secret.display_name} (${secret.type})`,
			value: id
		}));
	});
</script>

<div class="flex w-full gap-2 items-center">
	<div class="flex-grow">
		<Select {value} on:change={internalChange} {disabled} items={selectItems}></Select>
	</div>
	{#if value}
		<Button on:click={openEditModal} {disabled} size="sm">
			{$t('secrets.edit')}
		</Button>
	{:else}
		<Button on:click={openCreateModal} {disabled} size="sm">
			{$t('secrets.create')}
		</Button>
	{/if}
</div>

{#if showEditModal}
	<SecretEditModal
		bind:open={showEditModal}
		{isCreating}
		secretId={value}
		bind:editedSecretName
		bind:editedSecretType
		bind:editedSingleLineValue
		bind:editedMultiLineValue
		bind:editedFileValue
		bind:editedEnvVarList
		bind:editedFileInfo
		{includeInImage}
		{editedProcessingType}
		bind:isLoadingFile
		{allowedTypes}
		on:close={() => {
			resetFileInputById('fileValue');
			showEditModal = false;
		}}
		on:saved={handleSaved}
		on:error={handleError}
		on:download={downloadFile}
		on:fileChange={handleFileChange}
		on:addEnvVariable={addEnvVariable}
		on:removeEnvVariable={(e) => removeEnvVariable(e.detail)}
	/>
{/if}
