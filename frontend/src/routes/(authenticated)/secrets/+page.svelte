<script lang="ts">
	import { t } from 'svelte-i18n';
	import { onMount } from 'svelte';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import {
		Button,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell,
		Modal,
		Label,
		Input,
		Textarea,
		Select,
		Spinner
	} from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import type { ChangeEventHandler } from 'svelte/elements';

	export let data: PageData;

	type SecretType = 'single_line' | 'multi_line' | 'env_list' | 'file';

	type SecretShort = {
		id: string;
		display_name: string;
		type: SecretType;
		value_str?: string;
		value_size: number;
		filename?: string;
		created_at: string;
		updated_at: string;
		delete_at?: string | null;
	};

	type CreateSecretRequest = {
		display_name: string;
		type: SecretType;
		value_str?: string;
		value_b64?: string;
		filename?: string;
	};

	// Dictionary mapping UUIDs to secrets
	let secrets: Record<string, SecretShort> = {};
	let showEditModal = false;
	let currentSecretId: string | null = null;
	let editedSecretName = '';
	let lastEditedSecretType: SecretType = 'single_line';
	let editedSecretType: SecretType = 'single_line';
	let editedSingleLineValue: string | null = null;
	let editedMultiLineValue: string | undefined = undefined;
	let editedFileValue: File | null = null;
	let editedEnvVarList: [string, string][] | null = null;
	let editedFileInfo = { name: '', size: 0 };
	let isLoadingFile = false;

	const stringToEnvVars = (str: string): [string, string][] => {
		return str.split('\n').map((line) => {
			const [key, value] = line.split('=');
			return [key.trim(), value.trim()];
		});
	};

	const envVarsToString = (envVars: [string, string][]): string => {
		return envVars.map(([key, value]) => `${key}=${value}`).join('\n');
	};

	$: secrets = data.secrets;

	// Functions to work with the new data structure
	const changeSecretName = (id: string, newName: string): void => {
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

		// Update the secret name
		secrets[id] = { ...secret, display_name: newName };
		secrets = { ...secrets }; // Trigger reactivity
	};

	const openEditSecret = async (id: string): Promise<void> => {
		const secret = secrets[id];
		if (!secret) return;

		currentSecretId = id;
		editedSecretName = secret.display_name;
		editedSecretType = secret.type;

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

			// If file content isn't loaded, we don't need to do anything
			// It will be requested only when downloading or viewing
		}

		showEditModal = true;
	};

	const copySecretId = (id: string): void => {
		const secret = secrets[id];
		if (secret) {
			// Copy by name for template usage
			// navigator.clipboard.writeText(`\${secrets.${secret.name}}`);
			// Alternative: Show a dropdown with options to copy by ID or name
			navigator.clipboard.writeText(
				JSON.stringify({
					secret_id: secret.id
				})
			);
		}
	};

	const deleteSecret = (id: string): void => {
		if (confirm($t('secrets.confirm-delete'))) {
			const { [id]: _, ...remainingSecrets } = secrets;
			secrets = remainingSecrets;
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
		editedEnvVarList = null;
		showEditModal = true;
	};

	const _arrayBufferToBase64 = (buffer: ArrayBuffer) => {
		var binary = '';
		var bytes = new Uint8Array(buffer);
		var len = bytes.byteLength;
		for (var i = 0; i < len; i++) {
			binary += String.fromCharCode(bytes[i]);
		}
		return window.btoa(binary);
	};

	const handleFileChange = (event: Event) => {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			editedFileValue = input.files[0];
			editedFileInfo = {
				name: input.files[0].name,
				size: input.files[0].size
			};
		}
	};

	const saveSecret = async (): Promise<void> => {
		if (editedSecretName.trim() === '') {
			alert($t('secrets.name-required'));
			return;
		}

		// Check for duplicate name (except when editing the current secret)
		const nameExists = Object.values(secrets).some(
			(s) => s.display_name === editedSecretName && (!currentSecretId || s.id !== currentSecretId)
		);

		if (nameExists) {
			alert($t('secrets.name-exists'));
			return;
		}

		let newSecret: CreateSecretRequest | null = null;

		switch (editedSecretType) {
			case 'single_line':
				newSecret = {
					display_name: editedSecretName,
					type: 'single_line',
					value_str: editedSingleLineValue || ''
				};
				break;

			case 'multi_line':
				newSecret = {
					display_name: editedSecretName,
					type: 'multi_line',
					value_str: editedMultiLineValue || ''
				};
				break;

			case 'env_list':
				newSecret = {
					display_name: editedSecretName,
					type: 'env_list',
					value_str: envVarsToString(editedEnvVarList || [])
				};
				break;

			case 'file':
				if (editedFileValue) {
					// New file uploaded, process it
					const arrayBuffer = await editedFileValue.arrayBuffer();
					newSecret = {
						display_name: editedSecretName,
						type: 'file',
						filename: editedFileValue.name,
						value_b64: _arrayBufferToBase64(arrayBuffer)
					};
				} else if (currentSecretId) {
					// Editing existing file secret without changing the file
					const existingSecret = secrets[currentSecretId];
					if (existingSecret && existingSecret.type === 'file') {
						newSecret = {
							...existingSecret,
							display_name: editedSecretName
						};
						break;
					}
				} else {
					alert($t('secrets.file-required'));
					return;
				}
				break;

			default:
				return;
		}

		if (!newSecret) return;

		// Update the secrets dictionary by creating or updating (depends on wether currentSecretId is null)
		if (currentSecretId) {
			await fetch(`/api/secrets/${currentSecretId}`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(newSecret)
			});
		} else {
			await fetch('/api/secrets', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(newSecret)
			});
		}
		await invalidate('/api/secrets');

		// Close the modal
		showEditModal = false;
	};
</script>

<PageHead title={$t('nav.secrets')} repoStatus={data.repoStatus} />

<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2">{$t('secrets.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('secrets.type')}</TableHeadCell>
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
					<div class="flex gap-1">
						<Button size="xs" on:click={() => openEditSecret(id)}>
							{$t('secrets.edit')}
						</Button>
						<Button
							size="xs"
							on:click={() => copySecretId(id)}
							title={`Copy \${secrets.${secret.display_name}}`}
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
				<TableBodyCell colspan={3} class="text-center p-4">
					{$t('secrets.no-secrets')}
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<div class="flex justify-between mt-4">
	<Button color="alternative" on:click={() => addSecret()}>
		+ {$t('secrets.add-secret')}
	</Button>
</div>

<!-- Edit Secret Modal -->
<Modal
	bind:open={showEditModal}
	title={currentSecretId ? $t('secrets.edit-secret') : $t('secrets.add-secret')}
	size="lg"
>
	<div class="space-y-4">
		<div>
			<Label for="secretName">{$t('secrets.name')}</Label>
			<Input
				id="secretName"
				bind:value={editedSecretName}
				placeholder={$t('secrets.name-placeholder')}
			/>
		</div>

		<div>
			<Label for="secretType">
				{$t('secrets.type')}
			</Label>
			<div class="flex items-center">
				{#if editedSecretType === 'single_line'}
					{$t('secrets.type-single-line')}
				{:else if editedSecretType === 'multi_line'}
					{$t('secrets.type-multi-line')}
				{:else if editedSecretType === 'env_list'}
					{$t('secrets.type-env-list')}
				{:else if editedSecretType === 'file'}
					{$t('secrets.type-file')}
				{/if}
			</div>
		</div>
		{#if editedSecretType === 'single_line'}
			<div>
				<Label for="singleLineValue">{$t('secrets.value')}</Label>
				<Input id="singleLineValue" bind:value={editedSingleLineValue} />
			</div>
		{:else if editedSecretType === 'multi_line'}
			<div>
				<Label for="multiLineValue">{$t('secrets.value')}</Label>
				<Textarea id="multiLineValue" bind:value={editedMultiLineValue} rows={5} />
			</div>
		{:else if editedSecretType === 'file'}
			<div>
				<Label for="fileValue">{$t('secrets.file')}</Label>
				<Input id="fileValue" type="file" on:change={handleFileChange} />
				{#if editedFileInfo.name}
					<div class="mt-2 text-sm">
						<p>{$t('secrets.filename')}: {editedFileInfo.name}</p>
						<p>{$t('secrets.filesize')}: {(editedFileInfo.size / 1024).toFixed(2)} KB</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<svelte:fragment slot="footer">
		<Button on:click={saveSecret}>{$t('common.save')}</Button>
		<Button color="alternative" on:click={() => (showEditModal = false)}
			>{$t('common.cancel')}</Button
		>
	</svelte:fragment>
</Modal>
