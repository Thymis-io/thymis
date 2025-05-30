<script lang="ts">
	import { t } from 'svelte-i18n';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import { Button, Table, TableBodyCell, TableHead, TableHeadCell } from 'flowbite-svelte';
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

<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('artifacts.table.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('artifacts.table.type')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('artifacts.table.size')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('artifacts.table.usage')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('artifacts.table.created-at')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('artifacts.table.modified-at')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('artifacts.table.actions')}</TableHeadCell>
	</TableHead>
	<tbody>
		{#each data.artifacts as artifact (artifact.name)}
			<tr
				class="h-12 border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
			>
				<TableBodyCell tdClass="p-2"></TableBodyCell>
				<TableBodyEditCell
					value={artifact.name}
					onEnter={(value) => renameArtifact(artifact, value)}
				/>
				<TableBodyCell tdClass="p-2">
					{artifact.media_type || $t('artifacts.table.unknown-type')}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{bytesToHumanReadable(artifact.size)}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2 ">
					<div class="flex flex-row flex-wrap gap-2 items-center">
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
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{new Date(artifact.created_at).toLocaleString()}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{new Date(artifact.modified_at).toLocaleString()}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<Button
						class="px-2 py-1.5 gap-2 justify-start"
						color="alternative"
						href={`/api/artifacts/${artifact.name}`}
						download
					>
						<Download size={16} class="inline mr-1" />
						{$t('artifacts.table.download')}
					</Button>
					<Button
						class="px-2 py-1.5 gap-2 justify-start"
						color="alternative"
						onclick={() => (deleteConfirmTarget = artifact)}
					>
						<Trash size={16} class="inline mr-1" />
						{$t('artifacts.table.delete')}
					</Button>
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>

<div class="flex gap-2 mt-2">
	<input
		id="fileUpload"
		type="file"
		bind:files
		class="rounded-md border border-dashed border-gray-300 dark:border-gray-600 playwright-snapshot-unstable"
	/>
	<Button
		class="whitespace-nowrap"
		color="alternative"
		disabled={!files || files.length === 0}
		on:click={uploadFiles}
	>
		{$t('artifacts.upload-file')}
	</Button>
</div>
