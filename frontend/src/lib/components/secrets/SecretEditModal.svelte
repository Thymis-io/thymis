<script lang="ts">
	import { t } from 'svelte-i18n';
	import { createEventDispatcher } from 'svelte';
	import {
		Button,
		Modal,
		Label,
		Input,
		Textarea,
		Select,
		Checkbox,
		Spinner
	} from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import type { SecretProcessingType, SecretType } from '$lib/state';
	import { createSecretRequest, sendSecretRequest } from './secretUtils';

	interface Props {
		open?: boolean;
		isCreating?: boolean;
		editedSecretName?: string;
		editedSecretType?: SecretType;
		editedSingleLineValue?: string | null;
		editedMultiLineValue?: string | undefined;
		editedFileValue?: File | null;
		editedEnvVarList?: [string, string][] | null;
		editedFileInfo?: any;
		includeInImage?: boolean;
		editedProcessingType?: SecretProcessingType;
		isLoadingFile?: boolean;
		allowedTypes?: SecretType[];
		secretId?: string | null;
	}

	let {
		open = $bindable(false),
		isCreating = false,
		editedSecretName = $bindable(''),
		editedSecretType = $bindable('single_line'),
		editedSingleLineValue = $bindable(null),
		editedMultiLineValue = $bindable(undefined),
		editedFileValue = $bindable(null),
		editedEnvVarList = $bindable([['', '']]),
		editedFileInfo = $bindable({ name: '', size: 0 }),
		includeInImage = $bindable(false),
		editedProcessingType = $bindable('none'),
		isLoadingFile = $bindable(false),
		allowedTypes = ['single_line', 'multi_line', 'env_list', 'file'],
		secretId = null
	}: Props = $props();

	const dispatch = createEventDispatcher<{
		close: void;
		saved: { id: string; display_name: string };
		download: void;
		fileChange: Event;
		addEnvVariable: void;
		removeEnvVariable: number;
		error: string;
	}>();

	function handleFileChange(event: Event) {
		const target = event.target as HTMLInputElement;
		if (target.files && target.files.length > 0) {
			editedFileValue = target.files[0];
		}
		dispatch('fileChange', event);
	}

	function addEnvVariable() {
		dispatch('addEnvVariable');
	}

	function removeEnvVariable(index: number) {
		dispatch('removeEnvVariable', index);
	}

	async function onSave() {
		try {
			// Input validation
			if (editedSecretName.trim() === '') {
				dispatch('error', 'Name is required');
				return;
			}

			const editState = {
				secretName: editedSecretName,
				secretType: editedSecretType,
				singleLineValue: editedSingleLineValue,
				multiLineValue: editedMultiLineValue,
				fileValue: editedFileValue,
				envVarList: editedEnvVarList,
				fileInfo: editedFileInfo,
				includeInImage: includeInImage,
				processingType: editedProcessingType
			};

			// Create request data
			const secretData = await createSecretRequest(editState);
			if (!secretData) {
				dispatch('error', 'Failed to create secret request');
				return;
			}

			// Special handling for file type secrets with no file provided
			if (editedSecretType === 'file' && !editedFileValue && isCreating) {
				dispatch('error', 'File is required for new file secret');
				return;
			}

			// Send the request
			const result = await sendSecretRequest(secretId, secretData);

			if (!result.success) {
				dispatch('error', result.error || 'Failed to save secret');
				return;
			}

			// Notify parent of successful save
			dispatch('saved', {
				id: result.id!,
				display_name: result.display_name!
			});
		} catch (error) {
			console.error('Error saving secret:', error);
			dispatch('error', error instanceof Error ? error.message : 'Unknown error occurred');
		}
	}

	function onDownload() {
		dispatch('download');
	}

	function onClose() {
		dispatch('close');
	}

	// Filter the secret types based on allowed types
	let secretTypeOptions = $derived(
		[
			{ value: 'single_line', name: $t('secrets.type-single-line') },
			{ value: 'multi_line', name: $t('secrets.type-multi-line') },
			{ value: 'env_list', name: $t('secrets.type-env-list') },
			{ value: 'file', name: $t('secrets.type-file') }
		].filter((type) => allowedTypes.includes(type.value as SecretType))
	);

	// Ensure the initially selected type is allowed
	$effect(() => {
		if (!allowedTypes.includes(editedSecretType)) {
			editedSecretType = allowedTypes[0];
		}
	});

	// Make sure the editedProcessingType and includeInImage are properly initialized
	$effect(() => {
		if (!editedProcessingType) {
			editedProcessingType = 'none';
		}
	});
</script>

<Modal
	bind:open
	title={isCreating ? $t('secrets.create') : $t('secrets.edit')}
	size="lg"
	on:close={onClose}
	classDialog="secret-modal-dialog"
>
	<div class="space-y-4">
		<!-- Secret name -->
		<div>
			<Label for="secretName">{$t('secrets.name')}</Label>
			<Input
				id="secretName"
				bind:value={editedSecretName}
				placeholder={$t('secrets.name-placeholder')}
			/>
		</div>

		<!-- Secret type (only selectable when creating) -->
		<div>
			<Label for="secretType">{$t('secrets.type')}</Label>
			<Select id="secretType" bind:value={editedSecretType} disabled={!isCreating}>
				{#each secretTypeOptions as option}
					<option value={option.value}>{option.name}</option>
				{/each}
			</Select>
		</div>

		<!-- Processing type -->
		<div>
			<Label for="processingType">{$t('secrets.processing')}</Label>
			<Select
				id="processingType"
				bind:value={editedProcessingType}
				items={[
					{
						value: 'none',
						name: $t('secrets.processing-none')
					},
					{
						value: 'mkpasswd-yescrypt',
						name: $t('secrets.processing-mkpasswd-yescrypt')
					}
				]}
			></Select>
			{#if editedProcessingType === 'mkpasswd-yescrypt'}
				<p class="mt-1 text-xs text-gray-500">
					{$t('secrets.processing-description-yescrypt')}
				</p>
			{/if}
		</div>

		<!-- Include in image -->
		<div class="flex items-center space-x-2">
			<Checkbox id="includeInImage" bind:checked={includeInImage} />
			<Label for="includeInImage" class="flex">
				{$t('secrets.include-in-image')}
				<span class="ml-1 text-xs text-red-500">({$t('secrets.security-warning')})</span>
			</Label>
		</div>

		<!-- Type-specific value editors -->
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

				{#if !isCreating && editedFileInfo.name}
					<div class="mb-2 text-sm bg-gray-100 p-2 rounded">
						<p>
							<strong>{$t('secrets.current-file')}:</strong>
							{editedFileInfo.name} ({(editedFileInfo.size / 1024).toFixed(2)} KB)
						</p>

						<!-- Download button -->
						<div class="mt-3">
							<Button
								size="xs"
								color="blue"
								class="w-full"
								disabled={isLoadingFile}
								on:click={onDownload}
							>
								{#if isLoadingFile}
									<Spinner class="mr-2" size="4" />
								{/if}
								<span class="flex items-center">
									<Download class="mr-2" />
									{$t('secrets.download-file')}
								</span>
							</Button>
						</div>
					</div>
				{/if}

				<Input
					id="fileValue"
					type="file"
					on:change={handleFileChange}
					class="playwright-snapshot-unstable"
				/>

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
		<Button on:click={onSave}>{$t('common.save')}</Button>
		<Button color="alternative" on:click={onClose}>{$t('common.cancel')}</Button>
	</svelte:fragment>
</Modal>

<style>
	:global(.secret-modal-dialog > div) {
		max-height: 100% !important;
	}
</style>
