<script lang="ts">
	import { t } from 'svelte-i18n';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import SecretEditModal from '$lib/components/secrets/SecretEditModal.svelte';
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

<PageHead
	title={$t('nav.secrets')}
	globalState={data.globalState}
	nav={data.globalState}
	repoStatus={data.repoStatus}
>
	{#snippet actions()}
		<button class="ds-btn ds-btn-primary whitespace-nowrap" onclick={() => addSecret()}>
			+ {$t('secrets.create')}
		</button>
	{/snippet}
</PageHead>

<div class="ds-table-wrap">
	<table class="ds-table">
		<thead>
			<tr>
				<th>{$t('secrets.name')}</th>
				<th>{$t('secrets.type')}</th>
				<th>{$t('secrets.processing')}</th>
				<th>{$t('secrets.include-in-image')}</th>
				<th>{$t('secrets.issues')}</th>
				<th class="text-right">{$t('secrets.actions')}</th>
			</tr>
		</thead>
		<tbody>
			{#each Object.entries(secrets) as [id, secret]}
				<tr>
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
						<div class="flex justify-end gap-2">
							<button class="ds-btn ds-btn-sm" onclick={() => openEditSecret(id)}>
								{$t('secrets.edit')}
							</button>
							<button
								class="ds-btn ds-btn-sm"
								onclick={() => copySecretId(id)}
								title={`Copy ${secret.display_name} ID`}
								aria-label={`Copy ${secret.display_name} ID`}
							>
								{$t('secrets.copy-id')}
							</button>
							<button class="ds-btn ds-btn-sm ds-btn-danger" onclick={() => deleteSecret(id)}>
								{$t('secrets.delete')}
							</button>
						</div>
					</td>
				</tr>
			{:else}
				<tr>
					<td colspan={6} class="ds-table-empty">{$t('secrets.no-secrets')}</td>
				</tr>
			{/each}
		</tbody>
	</table>
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
