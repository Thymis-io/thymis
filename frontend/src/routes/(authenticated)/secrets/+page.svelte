<script lang="ts">
	import { t } from 'svelte-i18n';
	import Page from '$lib/components/layout/Page.svelte';
	import CreateButton from '$lib/components/layout/CreateButton.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import ActionButton from '$lib/components/layout/ActionButton.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import SecretEditModal from '$lib/components/secrets/SecretEditModal.svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import {
		downloadSecretFile,
		resetFileInputById,
		stringToEnvVars
	} from '$lib/components/secrets/secretUtils';
	import type { SecretProcessingType, SecretType } from '$lib/state';
	import Alert from 'lucide-svelte/icons/triangle-alert';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// State variables using const where appropriate
	let showCreateModal = $state(false);
	let showEditModal = $state(false);
	let currentSecretId: string | null = $state(null);
	let editedSecretName = $state('');
	let editedSecretType: SecretType = $state('single_line');
	let editedSingleLineValue: string | null = $state(null);
	let editedMultiLineValue: string | undefined = $state(undefined);
	let editedFileValue: File | null = $state(null);
	let editedEnvVarList: [string, string][] | null = $state(null);
	let editedFileInfo = $state({ name: '', size: 0 });
	let isLoadingFile = $state(false);
	let includeInImage = $state(false);
	let editedProcessingType: SecretProcessingType = $state('none');

	let secrets = $derived(data.secrets);

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

	let secretToDelete: { id: string; name: string } | undefined = $state(undefined);

	const deleteSecret = async (id: string): Promise<void> => {
		try {
			await fetch(`/api/secrets/${id}`, { method: 'DELETE' });
			await invalidate('/api/secrets');
		} catch (error) {
			console.error('Error deleting secret:', error);
			alert($t('secrets.delete-error'));
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

<Page title={$t('nav.secrets')} subtitle={$t('secrets.subtitle')}>
	{#snippet actions()}
		<CreateButton label={$t('secrets.create')} onclick={() => addSecret()} />
	{/snippet}

	<DataTable
		columns={[
			{ label: $t('secrets.name') },
			{ label: $t('secrets.type') },
			{ label: $t('secrets.processing') },
			{ label: $t('secrets.include-in-image') },
			{ label: $t('secrets.issues') },
			{ label: $t('secrets.actions'), align: 'right' }
		]}
		rows={Object.entries(secrets)}
		empty={$t('secrets.no-secrets')}
	>
		{#snippet row([id, secret])}
			<td>{secret.display_name}</td>
			<td>
				{#if secret.type === 'single_line'}
					{$t('secrets.type-single-line')}
				{:else if secret.type === 'multi_line'}
					{$t('secrets.type-multi-line')}
				{:else if secret.type === 'env_list'}
					{$t('secrets.type-env-list')}
				{:else if secret.type === 'file'}
					{$t('secrets.type-file')}
				{/if}
			</td>
			<td>
				{#if secret.processing_type === 'none'}
					{$t('secrets.processing-none')}
				{:else if secret.processing_type === 'mkpasswd-yescrypt'}
					{$t('secrets.processing-mkpasswd-yescrypt')}
				{/if}
			</td>
			<td>
				{secret.include_in_image ? $t('common.yes') : $t('common.no')}
			</td>
			<td>
				{#if secret.error}
					<div class="flex items-center gap-1" style="color: var(--ds-warning)">
						<Alert size="16" />
						{secret.error}
					</div>
				{/if}
			</td>
			<td>
				<RowActions>
					<ActionButton label={$t('secrets.edit')} onclick={() => openEditSecret(id)} />
					<ActionButton
						label={$t('secrets.copy-id')}
						onclick={() => copySecretId(id)}
						title={`Copy ${secret.display_name} ID`}
						aria-label={`Copy ${secret.display_name} ID`}
					/>
					<ActionButton
						label={$t('secrets.delete')}
						variant="danger"
						onclick={() => (secretToDelete = { id, name: secret.display_name })}
					/>
				</RowActions>
			</td>
		{/snippet}
	</DataTable>

	<DeleteConfirm
		target={secretToDelete?.name}
		on:confirm={() => {
			if (secretToDelete) deleteSecret(secretToDelete.id);
			secretToDelete = undefined;
		}}
		on:cancel={() => (secretToDelete = undefined)}
	/>

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
</Page>
