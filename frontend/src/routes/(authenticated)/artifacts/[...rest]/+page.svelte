<script lang="ts">
	import { t } from 'svelte-i18n';
	import Page from '$lib/components/layout/Page.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import CreateButton from '$lib/components/layout/CreateButton.svelte';
	import RowMenu from '$lib/components/layout/RowMenu.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import { Button, Helper, Modal } from 'flowbite-svelte';
	import Trash from 'lucide-svelte/icons/trash-2';
	import Download from 'lucide-svelte/icons/download';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import type { Artifact } from './+page';
	import Pen from 'lucide-svelte/icons/pen';
	import type { ModuleSettings } from '$lib/state';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let files = $state<FileList>();
	let uploadReplaceFile = $state<File | null>(null);
	let deleteConfirmTarget = $state<Artifact | undefined>();
	let showUploadModal = $state(false);
	let editArtifact = $state<Artifact | undefined>();
	let editArtifactName = $state('');

	const uploadFiles = async () => {
		if (!files || files.length === 0) return;

		const formData = new FormData();
		for (const file of files) {
			formData.append('files', file);
		}

		await fetch(`/api/artifacts/`, {
			method: 'POST',
			body: formData
		});

		await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
		const input = document.getElementById('fileUpload') as HTMLInputElement | null;
		if (input) input.value = '';
		files = undefined;
		showUploadModal = false;
		uploadReplaceFile = null;
	};

	const submitUpload = () => {
		if (!files || files.length === 0) return;
		if (isUnusedName(null, files[0].name)) {
			uploadFiles();
		} else {
			showUploadModal = false;
			uploadReplaceFile = files[0];
		}
	};

	const closeUploadModal = () => {
		files = undefined;
		showUploadModal = false;
	};

	const bytesToHumanReadable = (bytes: number): string => {
		if (bytes < 1000) return `${bytes} B`;
		if (bytes < 1000000) return `${(bytes / 1000).toFixed(2)} KB`;
		if (bytes < 1000000000) return `${(bytes / 1000000).toFixed(2)} MB`;
		return `${(bytes / 1000000000).toFixed(2)} GB`;
	};

	const isUnusedName = (artifact: Artifact | null, newName: string): boolean => {
		if (!newName || newName.trim() === '') return false;
		return !data.artifacts.some((a) => a != artifact && a.name === newName);
	};

	const renameArtifact = async (artifact: Artifact, newName: string) => {
		if (!newName || newName.trim() === '') return;

		await fetch(`/api/artifacts/rename/${artifact.name}?new_name=${newName}`, {
			method: 'POST'
		});

		await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
	};

	const openEditArtifact = (artifact: Artifact) => {
		editArtifact = artifact;
		editArtifactName = artifact.name;
	};

	const editNameValid = $derived(
		!!editArtifact &&
			!!editArtifactName.trim() &&
			(editArtifactName.trim() === editArtifact.name ||
				isUnusedName(editArtifact, editArtifactName.trim()))
	);

	const submitEditArtifact = async () => {
		if (!editArtifact || !editNameValid) return;
		const newName = editArtifactName.trim();
		if (newName !== editArtifact.name) {
			await renameArtifact(editArtifact, newName);
		}
		editArtifact = undefined;
	};

	const deleteArtifact = async (artifact: Artifact) => {
		await fetch(`/api/artifacts/${artifact.name}`, {
			method: 'DELETE'
		});

		await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
	};

	const hasArtifactUsages = (artifact: Artifact, module: ModuleSettings): boolean => {
		const isArtifact = (key: string, value: unknown): boolean => {
			if (key === 'artifact' && value === artifact.name) {
				return true;
			}
			if (key === 'artifacts' && Array.isArray(value) && value.includes(artifact.name)) {
				return true;
			}
			if (value !== null && typeof value === 'object') {
				return Object.entries(value).some(([subKey, subValue]) => isArtifact(subKey, subValue));
			}
			if (value !== null && Array.isArray(value)) {
				return value.some((element) => isArtifact(key, element));
			}
			return false;
		};

		return Object.entries(module.settings).some(([key, value]) => isArtifact(key, value));
	};
</script>

<Page title={$t('nav.artifacts')} subtitle={$t('artifacts.subtitle')}>
	{#snippet actions()}
		<CreateButton
			label={$t('artifacts.upload-file')}
			onclick={() => {
				files = undefined;
				showUploadModal = true;
			}}
		/>
	{/snippet}

	<DeleteConfirm
		target={deleteConfirmTarget?.name}
		on:cancel={() => (deleteConfirmTarget = undefined)}
		on:confirm={() => deleteConfirmTarget && deleteArtifact(deleteConfirmTarget)}
	/>

	<Modal
		bind:open={showUploadModal}
		title={$t('artifacts.upload-title')}
		outsideclose
		on:close={closeUploadModal}
	>
		<div class="space-y-4">
			<p class="text-sm" style="color: var(--ds-text-dim)">
				{$t('artifacts.upload-description')}
			</p>
			<input
				id="fileUpload"
				type="file"
				multiple
				bind:files
				class="playwright-snapshot-unstable block w-full cursor-pointer rounded-lg border border-dashed border-[var(--ds-border-strong)] bg-[var(--ds-surface-2)] p-4 text-sm text-[var(--ds-text)]"
			/>
		</div>
		<svelte:fragment slot="footer">
			<Button color="alternative" on:click={closeUploadModal}>
				{$t('artifacts.replace-file-cancel')}
			</Button>
			<Button on:click={submitUpload} disabled={!files || files.length === 0}>
				{$t('artifacts.upload-file')}
			</Button>
		</svelte:fragment>
	</Modal>

	<Modal
		open={!!uploadReplaceFile}
		title={$t('artifacts.replace-file-title')}
		autoclose
		outsideclose
		on:close={() => (uploadReplaceFile = null)}
	>
		<div class="text-lg whitespace-pre-line">
			{$t('artifacts.replace-file-description', {
				values: { name: uploadReplaceFile?.name }
			})}
		</div>
		<div class="flex justify-end mt-4">
			<Button on:click={() => (uploadReplaceFile = null)} color="alternative">
				{$t('artifacts.replace-file-cancel')}
			</Button>
			<Button on:click={uploadFiles} color="red" class="ml-2">
				{$t('artifacts.replace-file-confirm')}
			</Button>
		</div>
	</Modal>

	<Modal
		open={!!editArtifact}
		title={$t('artifacts.edit-title')}
		outsideclose
		on:close={() => (editArtifact = undefined)}
	>
		<div class="space-y-2">
			<label class="ds-form-label" for="editArtifactName">{$t('artifacts.table.name')}</label>
			<input id="editArtifactName" class="ds-input" bind:value={editArtifactName} />
			{#if !editNameValid && editArtifactName.trim()}
				<Helper color="red">{$t('artifacts.name-already-used')}</Helper>
			{/if}
		</div>
		<svelte:fragment slot="footer">
			<Button color="alternative" on:click={() => (editArtifact = undefined)}>
				{$t('artifacts.replace-file-cancel')}
			</Button>
			<Button on:click={submitEditArtifact} disabled={!editNameValid}>
				{$t('common.save')}
			</Button>
		</svelte:fragment>
	</Modal>

	<DataTable
		columns={[
			{ label: $t('artifacts.table.name') },
			{ label: $t('artifacts.table.type') },
			{ label: $t('artifacts.table.size') },
			{ label: $t('artifacts.table.usage') },
			{ label: $t('artifacts.table.created-at') },
			{ label: $t('artifacts.table.modified-at') },
			{ label: $t('artifacts.table.actions'), align: 'right' }
		]}
		rows={data.artifacts}
		empty={$t('artifacts.empty')}
	>
		{#snippet row(artifact)}
			<td>
				<button
					class="ds-name-btn"
					onclick={() => openEditArtifact(artifact)}
					title={$t('artifacts.edit')}
				>
					{artifact.name}
				</button>
			</td>
			<td>{artifact.media_type || $t('artifacts.table.unknown-type')}</td>
			<td>{bytesToHumanReadable(artifact.size)}</td>
			<td>
				<div class="flex flex-row flex-wrap items-center gap-2">
					{#each data.globalState.configs as config}
						{#if config.modules.some((module) => hasArtifactUsages(artifact, module))}
							<IdentifierLink
								identifier={config.identifier}
								context="config"
								globalState={data.globalState}
								solidBackground
							/>
						{/if}
					{/each}
					{#each data.globalState.tags as tag}
						{#if tag.modules.some((module) => hasArtifactUsages(artifact, module))}
							<IdentifierLink
								identifier={tag.identifier}
								context="tag"
								globalState={data.globalState}
								solidBackground
							/>
						{/if}
					{/each}
				</div>
			</td>
			<td class="playwright-snapshot-unstable w-[10rem]">
				{new Date(artifact.created_at).toLocaleString()}
			</td>
			<td class="playwright-snapshot-unstable w-[10rem]">
				{new Date(artifact.modified_at).toLocaleString()}
			</td>
			<td>
				<RowActions>
					<RowMenu
						label={$t('artifacts.table.actions')}
						items={[
							{ label: $t('artifacts.edit'), icon: Pen, onclick: () => openEditArtifact(artifact) },
							{
								label: $t('artifacts.table.download'),
								icon: Download,
								href: `/api/artifacts/${artifact.name}`,
								download: true
							},
							{
								label: $t('artifacts.table.delete'),
								icon: Trash,
								variant: 'danger',
								onclick: () => (deleteConfirmTarget = artifact)
							}
						]}
					/>
				</RowActions>
			</td>
		{/snippet}
	</DataTable>
</Page>
