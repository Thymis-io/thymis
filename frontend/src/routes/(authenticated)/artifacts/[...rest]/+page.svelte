<script lang="ts">
	import { t } from 'svelte-i18n';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import { Button, Helper, Modal } from 'flowbite-svelte';
	import Trash from 'lucide-svelte/icons/trash-2';
	import Download from 'lucide-svelte/icons/download';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import type { Artifact } from './+page';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import type { ModuleSettings } from '$lib/state';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let files = $state<FileList>();
	let uploadReplaceFile = $state<File | null>(null);
	let deleteConfirmTarget = $state<Artifact | undefined>();

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
		(document.getElementById('fileUpload') as HTMLInputElement).value = '';
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

<PageHead
	title={$t('nav.artifacts')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

<DeleteConfirm
	target={deleteConfirmTarget?.name}
	on:cancel={() => (deleteConfirmTarget = undefined)}
	on:confirm={() => deleteConfirmTarget && deleteArtifact(deleteConfirmTarget)}
/>

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

<div class="ds-table-wrap">
	<table class="ds-table">
		<thead>
			<tr>
				<th class="w-12"></th>
				<th>{$t('artifacts.table.name')}</th>
				<th>{$t('artifacts.table.type')}</th>
				<th>{$t('artifacts.table.size')}</th>
				<th>{$t('artifacts.table.usage')}</th>
				<th>{$t('artifacts.table.created-at')}</th>
				<th>{$t('artifacts.table.modified-at')}</th>
				<th class="text-right">{$t('artifacts.table.actions')}</th>
			</tr>
		</thead>
		<tbody>
			{#each data.artifacts as artifact (artifact.name)}
				<tr>
					<td></td>
					<TableBodyEditCell
						value={artifact.name}
						onEnter={async (value) => {
							if (isUnusedName(artifact, value)) {
								renameArtifact(artifact, value);
							}

							// Reset the input field after renaming
							await invalidate((url) => url.pathname.startsWith('/api/artifacts'));
						}}
					>
						{#snippet bottom({ value: newName })}
							{#if !isUnusedName(artifact, newName)}
								<Helper color="red">
									{$t('artifacts.name-already-used')}
								</Helper>
							{/if}
						{/snippet}
					</TableBodyEditCell>
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
						<div class="flex justify-end gap-2">
							<a class="ds-btn ds-btn-sm" href={`/api/artifacts/${artifact.name}`} download>
								<Download size={15} />
								{$t('artifacts.table.download')}
							</a>
							<button
								class="ds-btn ds-btn-sm ds-btn-danger"
								onclick={() => (deleteConfirmTarget = artifact)}
							>
								<Trash size={15} />
								{$t('artifacts.table.delete')}
							</button>
						</div>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<div class="mt-4 flex items-center gap-2">
	<input
		id="fileUpload"
		type="file"
		bind:files
		class="playwright-snapshot-unstable rounded-md border border-dashed border-[var(--ds-border-strong)] p-2 text-sm"
	/>
	<button
		class="ds-btn whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-50"
		disabled={!files || files.length === 0}
		onclick={() => {
			if (!files) return;
			if (isUnusedName(null, files[0].name)) {
				uploadFiles();
			} else {
				uploadReplaceFile = files[0];
			}
		}}
	>
		{$t('artifacts.upload-file')}
	</button>
</div>
