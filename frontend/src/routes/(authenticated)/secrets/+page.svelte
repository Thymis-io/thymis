<script lang="ts">
	import { t } from 'svelte-i18n';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import {
		Button,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell
	} from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import SecretEditModal from '$lib/components/secrets/SecretEditModal.svelte';
	import { page } from '$app/stores';
	import {
		type SecretShort,
		type SecretEditState,
		createSecretRequest,
		downloadSecretFile,
		resetFileInputById,
		sendSecretRequest
	} from '$lib/components/secrets/secretUtils';
	import type { SecretProcessingType, SecretType } from '$lib/state';

	export let data: PageData;

	// State variables using const where appropriate
	let showCreateModal = false;
	let showEditModal = false;
	let currentSecretId: string | null = null;
	let editedSecretName = '';
	let editedSecretType: SecretType = 'single_line';
	let editedSingleLineValue: string | null = null;
	let editedMultiLineValue: string | undefined = undefined;
	let editedFileValue: File | null = null;
	let editedEnvVarList: [string, string][] | null = null;
	let editedFileInfo = { name: '', size: 0 };
	let isLoadingFile = false;
	let includeInImage = false;
	let editedProcessingType: SecretProcessingType = 'none';

	// Access secrets from $page.data
	$: secrets = $page.data.secrets;

	const changeSecretName = async (id: string, newName: string) => {
		const secret = secrets[id];
		if (!secret || secret.display_name === newName || newName.trim() === '') return;

		// Check if name already exists for another secret
		const nameExists = Object.values(secrets).some(
			(s) => s.display_name === newName && s.id !== id
		);
		if (nameExists) {
			alert($t('secrets.name-exists'));
			return;
		}

		// Update the secret using api

		await sendSecretRequest(id, { display_name: newName });
		await invalidate('/api/secrets');
	};

	const openEditSecret = async (id: string): Promise<void> => {
		const secret = secrets[id];
		if (!secret) return;

		// Make sure currentSecretId is properly set as a string
		currentSecretId = String(id);

		editedSecretName = secret.display_name;
		editedSecretType = secret.type;
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
			const envList = stringToEnvVars(secret.value_str || '');
			editedEnvVarList = envList.length > 0 ? envList : [['', '']];
		} else if (secret.type === 'file') {
			editedSingleLineValue = null;
			editedMultiLineValue = undefined;
			editedFileInfo = {
				name: secret.filename || '',
				size: secret.value_size
			};
			editedFileValue = null;
			editedEnvVarList = null;

			setTimeout(() => resetFileInputById('editFileValue'), 100);
		}

		showEditModal = true;
	};

	const copySecretId = (id: string): void => {
		const secret = secrets[id];
		if (secret) {
			navigator.clipboard.writeText(
				JSON.stringify({
					type: 'secret',
					value: id,
					secret_type: secret.type
				})
			);
		}
	};

	const deleteSecret = async (id: string): Promise<void> => {
		if (confirm($t('secrets.confirm-delete'))) {
			try {
				await fetch(`/api/secrets/${id}`, { method: 'DELETE' });
				await invalidate('/api/secrets');
			} catch (error) {
				console.error('Error deleting secret:', error);
				alert($t('secrets.delete-error'));
			}
		}
	};

	const addSecret = (): void => {
		const newName = `new_secret_${Object.keys(secrets).length + 1}`;
		currentSecretId = null;
		editedSecretName = newName;
		editedSecretType = 'single_line';
		editedSingleLineValue = '';
		editedMultiLineValue = undefined;
		editedFileValue = null;
		editedFileInfo = { name: '', size: 0 };
		editedEnvVarList = [['', '']]; // Initialize with an empty pair
		includeInImage = false;
		editedProcessingType = 'none';
		setTimeout(() => resetFileInputById('fileValue'), 100);
		showCreateModal = true;
	};

	function handleFileChange(event: Event) {
		const input = (event.detail?.target as HTMLInputElement) || (event.target as HTMLInputElement);
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

	function handleSaved() {
		invalidate('/api/secrets');
		showCreateModal = false;
		showEditModal = false;
	}

	function handleError(event: CustomEvent<string>) {
		alert($t('secrets.save-error') + (event.detail ? `: ${event.detail}` : ''));
	}

	const downloadFile = async () => {
		if (!currentSecretId || !editedFileInfo.name) return;

		isLoadingFile = true;
		try {
			const success = await downloadSecretFile(currentSecretId, editedFileInfo.name);
			if (!success) {
				alert($t('secrets.download-error'));
			}
		} finally {
			isLoadingFile = false;
		}
	};
</script>

<PageHead title={$t('nav.secrets')} repoStatus={data.repoStatus} />

<!-- Table structure remains the same -->
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2">{$t('secrets.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.type')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.processing')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.include-in-image')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each Object.entries(secrets) as [id, secret]}
			<TableBodyRow>
				<TableBodyEditCell
					bind:value={secret.display_name}
					onEnter={(newName) => changeSecretName(id, newName)}
				/>
				<TableBodyCell tdClass="p-2">
					{#if secret.type === 'single_line'}
						{$t('secrets.type-single-line')}
					{:else if secret.type === 'multi_line'}
						{$t('secrets.type-multi-line')}
					{:else if secret.type === 'env_list'}
						{$t('secrets.type-env-list')}
					{:else if secret.type === 'file'}
						{$t('secrets.type-file')}
					{/if}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{#if secret.processing_type === 'none'}
						{$t('secrets.processing-none')}
					{:else if secret.processing_type === 'mkpasswd-yescrypt'}
						{$t('secrets.processing-mkpasswd-yescrypt')}
					{/if}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{secret.include_in_image ? $t('common.yes') : $t('common.no')}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<div class="flex gap-1">
						<Button size="xs" on:click={() => openEditSecret(id)}>
							{$t('secrets.edit')}
						</Button>
						<Button
							size="xs"
							on:click={() => copySecretId(id)}
							title={`Copy ${secret.display_name} ID`}
							aria-label={`Copy ${secret.display_name} ID`}
						>
							{$t('secrets.copy-id')}
						</Button>

						<Button size="xs" color="red" on:click={() => deleteSecret(id)}>
							{$t('secrets.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</TableBodyRow>
		{:else}
			<TableBodyRow>
				<TableBodyCell colspan={5} class="text-center p-4">
					{$t('secrets.no-secrets')}
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<div class="flex justify-between mt-4">
	<Button color="alternative" on:click={() => addSecret()}>
		+ {$t('secrets.create')}
	</Button>
</div>

<!-- Create Secret Modal -->
<SecretEditModal
	bind:open={showCreateModal}
	isCreating={true}
	secretId={null}
	bind:editedSecretName
	bind:editedSecretType
	bind:editedSingleLineValue
	bind:editedMultiLineValue
	bind:editedFileValue
	bind:editedEnvVarList
	bind:editedFileInfo
	bind:includeInImage
	bind:editedProcessingType
	bind:isLoadingFile
	on:close={() => {
		resetFileInputById('fileValue');
		showCreateModal = false;
	}}
	on:saved={handleSaved}
	on:error={handleError}
	on:download={downloadFile}
	on:fileChange={handleFileChange}
	on:addEnvVariable={addEnvVariable}
	on:removeEnvVariable={(e) => removeEnvVariable(e.detail)}
/>

<!-- Edit Secret Modal -->
<SecretEditModal
	bind:open={showEditModal}
	isCreating={false}
	secretId={currentSecretId}
	bind:editedSecretName
	bind:editedSecretType
	bind:editedSingleLineValue
	bind:editedMultiLineValue
	bind:editedFileValue
	bind:editedEnvVarList
	bind:editedFileInfo
	bind:includeInImage
	bind:editedProcessingType
	bind:isLoadingFile
	on:close={() => {
		resetFileInputById('editFileValue');
		showEditModal = false;
	}}
	on:saved={handleSaved}
	on:error={handleError}
	on:download={downloadFile}
	on:fileChange={handleFileChange}
	on:addEnvVariable={addEnvVariable}
	on:removeEnvVariable={(e) => removeEnvVariable(e.detail)}
/>
