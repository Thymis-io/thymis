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
	let showCreateModal = false;
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
		if (!str || str.trim() === '') {
			return [['', '']]; // Default empty entry
		}

		return str
			.split('\n')
			.filter((line) => line.trim() !== '')
			.map((line) => {
				const separatorIndex = line.indexOf('=');
				if (separatorIndex === -1) {
					return [line.trim(), '']; // No value
				}
				const key = line.substring(0, separatorIndex).trim();
				const value = line.substring(separatorIndex + 1).trim();
				return [key, value];
			});
	};

	const envVarsToString = (envVars: [string, string][]): string => {
		if (!envVars || envVars.length === 0) {
			return '';
		}

		return envVars
			.filter(([key]) => key.trim() !== '') // Only include entries with non-empty keys
			.map(([key, value]) => `${key}=${value}`)
			.join('\n');
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

		// Make sure currentSecretId is properly set as a string
		currentSecretId = String(id);
		console.log('Opening edit for secret:', { id, currentSecretId, name: secret.display_name });

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
			// Parse environment variables with better handling
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

			// If file content isn't loaded, we don't need to do anything
			// It will be requested only when downloading or viewing
			setTimeout(() => resetFileInput('editFileValue'), 100);
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
		editedFileInfo = { name: '', size: 0 };
		editedEnvVarList = [['', '']]; // Initialize with an empty pair
		setTimeout(() => resetFileInput('fileValue'), 100);
		showCreateModal = true;
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
			console.log('File selected:', editedFileInfo);
		} else {
			console.log('No file selected');
		}
	};

	// Reset file input to avoid issues with the same file being selected twice
	const resetFileInput = (inputId: string) => {
		const fileInput = document.getElementById(inputId) as HTMLInputElement;
		if (fileInput) {
			fileInput.value = '';
		}
	};

	const saveSecret = async (): Promise<void> => {
		if (editedSecretName.trim() === '') {
			alert($t('secrets.name-required'));
			return;
		}

		// Enhanced debugging for saving
		console.log('Saving secret with:', {
			currentSecretId,
			editedSecretName,
			editedSecretType,
			secretsCount: Object.keys(secrets).length
		});

		// Special case: if currentSecretId exists and the name hasn't changed, skip the name check
		const currentSecret = currentSecretId ? secrets[currentSecretId] : null;
		if (currentSecret && currentSecret.display_name === editedSecretName) {
			console.log('Name unchanged, skipping conflict check');
			// Name hasn't changed, continue with the save
		} else {
			// Only check for conflicts if the name has actually changed
			let conflictDetected = false;

			// Debug check for all secrets
			console.log(
				'All secrets:',
				Object.entries(secrets).map(([id, s]) => ({
					id,
					name: s.display_name,
					matches_name: s.display_name === editedSecretName,
					matches_id: id === currentSecretId,
					would_conflict: s.display_name === editedSecretName && id !== currentSecretId
				}))
			);

			// Explicit for loop for better control
			for (const [id, secret] of Object.entries(secrets)) {
				if (secret.display_name === editedSecretName) {
					// If this is not the secret we're currently editing
					if (id !== currentSecretId) {
						console.log('Conflict found:', {
							existingId: id,
							currentId: currentSecretId,
							name: secret.display_name,
							areIdsEqual: id === currentSecretId
						});
						conflictDetected = true;
						break;
					}
				}
			}

			if (conflictDetected) {
				alert(`${$t('secrets.name-exists')}: "${editedSecretName}" ${$t('secrets.already-used')}`);
				return;
			}
		}

		let newSecret: CreateSecretRequest | null = null;

		try {
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
						try {
							console.log('Processing file upload:', editedFileInfo);
							const arrayBuffer = await editedFileValue.arrayBuffer();
							const base64Data = _arrayBufferToBase64(arrayBuffer);

							newSecret = {
								display_name: editedSecretName,
								type: 'file',
								filename: editedFileValue.name,
								value_b64: base64Data
							};
							console.log('File processed successfully');
						} catch (error) {
							console.error('Error processing file:', error);
							alert($t('secrets.file-processing-error'));
							return;
						}
					} else if (currentSecretId) {
						// Editing existing file secret without changing the file
						const existingSecret = secrets[currentSecretId];
						if (existingSecret && existingSecret.type === 'file') {
							newSecret = {
								display_name: editedSecretName,
								type: 'file',
								filename: existingSecret.filename
							};
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

			// Debug the payload being sent
			console.log('Sending payload:', newSecret);

			// Update the secrets dictionary by creating or updating (depends on wether currentSecretId is null)
			if (currentSecretId) {
				// log
				console.log('Updating existing secret:', { currentSecretId, newSecret });
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
			showCreateModal = false;
			showEditModal = false;
		} catch (error) {
			console.error('Error saving secret:', error);
			alert($t('secrets.save-error'));
			return;
		}
	};

	// Helper function to add an env variable pair
	const addEnvVariable = () => {
		editedEnvVarList = [...(editedEnvVarList || [['', '']]), ['', '']];
	};

	// Helper function to remove an env variable pair
	const removeEnvVariable = (index: number) => {
		if (editedEnvVarList && editedEnvVarList.length > 1) {
			const newList = [...editedEnvVarList];
			newList.splice(index, 1);
			editedEnvVarList = newList;
		} else {
			// Don't remove the last one, just clear it
			editedEnvVarList = [['', '']];
		}
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

<!-- Create Secret Modal -->
<Modal
	bind:open={showCreateModal}
	title={$t('secrets.add-secret')}
	size="lg"
	on:close={() => resetFileInput('fileValue')}
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
			<Select id="secretType" bind:value={editedSecretType}>
				<option value="single_line">{$t('secrets.type-single-line')}</option>
				<option value="multi_line">{$t('secrets.type-multi-line')}</option>
				<option value="env_list">{$t('secrets.type-env-list')}</option>
				<option value="file">{$t('secrets.type-file')}</option>
			</Select>
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
		{:else if editedSecretType === 'env_list'}
			<div>
				<Label>{$t('secrets.env-variables')}</Label>
				{#if !editedEnvVarList || editedEnvVarList.length === 0}
					{@const dummy = editedEnvVarList = [['', '']]}
				{/if}
				{#each editedEnvVarList as [key, value], i}
					<div class="flex gap-2 mb-2">
						<Input placeholder="KEY" bind:value={editedEnvVarList[i][0]} />
						<Input placeholder="VALUE" bind:value={editedEnvVarList[i][1]} />
						<Button size="xs" color="red" on:click={() => removeEnvVariable(i)}>X</Button>
					</div>
				{/each}
				<Button size="xs" on:click={addEnvVariable}>+ {$t('secrets.add-variable')}</Button>
			</div>
		{:else if editedSecretType === 'file'}
			<div>
				<Label for="fileValue">{$t('secrets.file')}</Label>
				<Input id="fileValue" type="file" on:change={handleFileChange} />
				{#if editedFileInfo.name}
					<div class="mt-2 text-sm bg-gray-100 p-2 rounded">
						<p><strong>{$t('secrets.filename')}:</strong> {editedFileInfo.name}</p>
						<p>
							<strong>{$t('secrets.filesize')}:</strong>
							{(editedFileInfo.size / 1024).toFixed(2)} KB
						</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<svelte:fragment slot="footer">
		<Button on:click={saveSecret}>{$t('common.save')}</Button>
		<Button color="alternative" on:click={() => (showCreateModal = false)}
			>{$t('common.cancel')}</Button
		>
	</svelte:fragment>
</Modal>

<!-- Edit Secret Modal -->
<Modal
	bind:open={showEditModal}
	title={$t('secrets.edit-secret')}
	size="lg"
	on:close={() => resetFileInput('editFileValue')}
>
	<div class="space-y-4">
		<div>
			<Label for="editSecretName">{$t('secrets.name')}</Label>
			<Input
				id="editSecretName"
				bind:value={editedSecretName}
				placeholder={$t('secrets.name-placeholder')}
			/>
		</div>

		<div>
			<Label for="secretTypeDisabled">
				{$t('secrets.type')}
			</Label>
			<div class="p-2 border border-gray-300 rounded-lg bg-gray-50">
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
				<Label for="editSingleLineValue">{$t('secrets.value')}</Label>
				<Input id="editSingleLineValue" bind:value={editedSingleLineValue} />
			</div>
		{:else if editedSecretType === 'multi_line'}
			<div>
				<Label for="editMultiLineValue">{$t('secrets.value')}</Label>
				<Textarea id="editMultiLineValue" bind:value={editedMultiLineValue} rows={5} />
			</div>
		{:else if editedSecretType === 'env_list'}
			<div>
				<Label>{$t('secrets.env-variables')}</Label>
				{#if !editedEnvVarList || editedEnvVarList.length === 0}
					{@const dummy = editedEnvVarList = [['', '']]}
				{/if}
				{#each editedEnvVarList as [key, value], i}
					<div class="flex gap-2 mb-2">
						<Input placeholder="KEY" bind:value={editedEnvVarList[i][0]} />
						<Input placeholder="VALUE" bind:value={editedEnvVarList[i][1]} />
						<Button size="xs" color="red" on:click={() => removeEnvVariable(i)}>X</Button>
					</div>
				{/each}
				<Button size="xs" on:click={addEnvVariable}>+ {$t('secrets.add-variable')}</Button>
			</div>
		{:else if editedSecretType === 'file'}
			<div>
				<Label for="editFileValue">{$t('secrets.file')}</Label>
				{#if editedFileInfo.name}
					<div class="mb-2 text-sm bg-gray-100 p-2 rounded">
						<p>
							<strong>{$t('secrets.current-file')}:</strong>
							{editedFileInfo.name} ({(editedFileInfo.size / 1024).toFixed(2)} KB)
						</p>
					</div>
				{/if}
				<Input id="editFileValue" type="file" on:change={handleFileChange} />
				{#if editedFileValue}
					<div class="mt-2 text-sm bg-green-100 p-2 rounded">
						<p>
							<strong>{$t('secrets.new-file')}:</strong>
							{editedFileValue.name} ({(editedFileValue.size / 1024).toFixed(2)} KB)
						</p>
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
