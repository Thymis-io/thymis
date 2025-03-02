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
		Select
	} from 'flowbite-svelte';
	import PageHead from '$lib/components/PageHead.svelte';
	import type { PageData } from './$types';

	export let data: PageData;

	// Secret type definitions
	type SecretType = 'single-line' | 'multi-line' | 'file';

	interface BaseSecret {
		type: SecretType;
	}

	interface SingleLineSecret extends BaseSecret {
		type: 'single-line';
		value: string;
	}

	interface MultiLineSecret extends BaseSecret {
		type: 'multi-line';
		value: string;
	}

	interface FileSecret extends BaseSecret {
		type: 'file';
		value: ArrayBuffer;
		filename: string;
		mimeType: string;
	}

	type Secret = SingleLineSecret | MultiLineSecret | FileSecret;

	type SecretEntry = [string, Secret];

	// Local state
	let secrets: SecretEntry[] = [];
	let showEditModal = false;
	let currentSecretName = '';
	let editedSecretName = '';
	let editedSecretType: SecretType = 'single-line';
	let editedSingleLineValue = '';
	let editedMultiLineValue = '';
	let editedFileValue: File | null = null;
	let editedFileInfo = { name: '', type: '', size: 0 };

	// Constants for functions to avoid recreating them
	const changeSecretName = (oldName: string, newName: string): void => {
		if (oldName === newName || newName.trim() === '') return;
		if (secrets.some(([name]) => name === newName)) {
			alert($t('secrets.name-exists'));
			return;
		}

		const index = secrets.findIndex(([name]) => name === oldName);
		if (index !== -1) {
			const secretValue = secrets[index][1];
			secrets.splice(index, 1);
			secrets = [...secrets, [newName, secretValue]];
		}
	};

	const openEditSecret = (name: string): void => {
		const secret = secrets.find(([secretName]) => secretName === name)?.[1];
		if (!secret) return;

		currentSecretName = name;
		editedSecretName = name;
		editedSecretType = secret.type;

		if (secret.type === 'single-line') {
			editedSingleLineValue = secret.value;
			editedMultiLineValue = '';
			editedFileValue = null;
		} else if (secret.type === 'multi-line') {
			editedSingleLineValue = '';
			editedMultiLineValue = secret.value;
			editedFileValue = null;
		} else if (secret.type === 'file') {
			editedSingleLineValue = '';
			editedMultiLineValue = '';
			editedFileInfo = {
				name: (secret as FileSecret).filename,
				type: (secret as FileSecret).mimeType,
				size: (secret as FileSecret).value.byteLength
			};
		}

		showEditModal = true;
	};

	const copySecretId = (name: string): void => {
		navigator.clipboard.writeText(`\${secrets.${name}}`);
	};

	const deleteSecret = (name: string): void => {
		if (confirm($t('secrets.confirm-delete'))) {
			secrets = secrets.filter(([secretName]) => secretName !== name);
		}
	};

	const addSecret = (): void => {
		const newName = `new_secret_${secrets.length + 1}`;
		currentSecretName = '';
		editedSecretName = newName;
		editedSecretType = 'single-line';
		editedSingleLineValue = '';
		editedMultiLineValue = '';
		editedFileValue = null;
		showEditModal = true;
	};

	const handleFileChange = (event: Event) => {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files.length > 0) {
			editedFileValue = input.files[0];
			editedFileInfo = {
				name: input.files[0].name,
				type: input.files[0].type,
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
		if (
			currentSecretName !== editedSecretName &&
			secrets.some(([name]) => name === editedSecretName)
		) {
			alert($t('secrets.name-exists'));
			return;
		}

		let newSecret: Secret;

		switch (editedSecretType) {
			case 'single-line':
				newSecret = {
					type: 'single-line',
					value: editedSingleLineValue
				};
				break;

			case 'multi-line':
				newSecret = {
					type: 'multi-line',
					value: editedMultiLineValue
				};
				break;

			case 'file':
				if (!editedFileValue) {
					// If editing an existing file secret, keep the old value
					if (currentSecretName) {
						const existingSecret = secrets.find(
							([name]) => name === currentSecretName
						)?.[1] as FileSecret;
						if (existingSecret && existingSecret.type === 'file') {
							newSecret = { ...existingSecret };
							break;
						}
					}
					alert($t('secrets.file-required'));
					return;
				}
				const arrayBuffer = await editedFileValue.arrayBuffer();
				newSecret = {
					type: 'file',
					value: arrayBuffer,
					filename: editedFileValue.name,
					mimeType: editedFileValue.type
				};
				break;

			default:
				return;
		}

		// If we're editing an existing secret, remove it first
		if (currentSecretName) {
			secrets = secrets.filter(([name]) => name !== currentSecretName);
		}

		// Add the new or updated secret
		secrets = [...secrets, [editedSecretName, newSecret]];

		// Close the modal
		showEditModal = false;
	};

	const convertValue = (): void => {
		// Handle conversion between secret types when type changes
		if (editedSecretType === 'single-line') {
			if (editedMultiLineValue) {
				// Convert multi-line to single-line
				editedSingleLineValue = editedMultiLineValue.split('\n')[0];
			}
		} else if (editedSecretType === 'multi-line') {
			if (editedSingleLineValue) {
				// Convert single-line to multi-line
				editedMultiLineValue = editedSingleLineValue;
			}
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
		{#each secrets as [name, secret]}
			<TableBodyRow>
				<TableBodyEditCell
					bind:value={name}
					onEnter={(newName) => changeSecretName(name, newName)}
				/>
				<TableBodyCell tdClass="p-2">
					{#if secret.type === 'single-line'}
						{$t('secrets.type-single-line')}
					{:else if secret.type === 'multi-line'}
						{$t('secrets.type-multi-line')}
					{:else if secret.type === 'file'}
						{$t('secrets.type-file')}
					{/if}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<div class="flex gap-1">
						<Button size="xs" on:click={() => openEditSecret(name)}>
							{$t('secrets.edit')}
						</Button>
						<Button size="xs" on:click={() => copySecretId(name)}>
							C
							{$t('secrets.copy-id')}
						</Button>
						<Button size="xs" color="red" on:click={() => deleteSecret(name)}>
							{$t('secrets.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</TableBodyRow>
		{:else}
			<TableBodyRow>
				<TableBodyCell colspan="3" class="text-center p-4">
					{$t('secrets.no-secrets')}
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<Button color="alternative" class="mt-4" on:click={() => addSecret()}>
	+ {$t('secrets.add-secret')}
</Button>

<!-- Edit Secret Modal -->
<Modal
	bind:open={showEditModal}
	title={currentSecretName ? $t('secrets.edit-secret') : $t('secrets.add-secret')}
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
			<Label for="secretType">{$t('secrets.type')}</Label>
			<Select id="secretType" bind:value={editedSecretType} on:change={convertValue}>
				<option value="single-line">{$t('secrets.type-single-line')}</option>
				<option value="multi-line">{$t('secrets.type-multi-line')}</option>
				<option value="file">{$t('secrets.type-file')}</option>
			</Select>
		</div>

		{#if editedSecretType === 'single-line'}
			<div>
				<Label for="singleLineValue">{$t('secrets.value')}</Label>
				<Input id="singleLineValue" bind:value={editedSingleLineValue} />
			</div>
		{:else if editedSecretType === 'multi-line'}
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
						<p>{$t('secrets.filetype')}: {editedFileInfo.type || $t('secrets.unknown')}</p>
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
