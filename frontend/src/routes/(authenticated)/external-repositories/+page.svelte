<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState } from '$lib/state';
	import { Modal, Spinner } from 'flowbite-svelte';
	import Page from '$lib/components/layout/Page.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import CreateButton from '$lib/components/layout/CreateButton.svelte';
	import RowMenu from '$lib/components/layout/RowMenu.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import type { PageData } from './$types';
	import Pen from 'lucide-svelte/icons/pen';
	import RefreshCw from 'lucide-svelte/icons/refresh-cw';
	import Trash from 'lucide-svelte/icons/trash-2';
	import EditExternalRepoUrl from '$lib/components/EditExternalRepoUrl.svelte';
	import ModuleIcon from '$lib/config/ModuleIcon.svelte';
	import DetailsModal from '$lib/components/DetailsModal.svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import RepoConnectionTest from '$lib/components/RepoConnectionTest.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let editModalOpen = $state(false);
	let creatingRepo = $state(false);
	let editRepoName = $state<string>();
	let editRepoUrl = $state<string>();
	let editRepoSecret = $state<string | null>();
	let detailsModalOpen = $state(false);
	let detailsText = $state<string>();
	let deleteRepoConfirm = $state<string>();
	let testConnectionOpen = $state(false);
	let testConnectionInput = $state<string>();
	let testConnectionApiSecret = $state<string | null>();

	const generateUniqueKey = () => {
		let num = 1;
		let key;

		do {
			key = `new-repo-${num}`;
			num++;
		} while (data.globalState.repositories[key]);

		return key;
	};

	// Adding a repo opens the edit modal first; the table entry is only created on save.
	const addRepo = () => {
		creatingRepo = true;
		editRepoName = generateUniqueKey();
		editRepoUrl = 'github:Thymis-io/thymis';
		editRepoSecret = null;
		editModalOpen = true;
	};

	const deleteRepo = (name: string) => {
		data.globalState.repositories = Object.fromEntries(
			Object.entries(data.globalState.repositories).filter(([key, value]) => key !== name)
		);

		saveState(data.globalState);
	};

	const changeRepoName = (oldName: string, newName: string) => {
		if (!data.globalState.repositories[newName]) {
			data.globalState.repositories = Object.fromEntries(
				Object.entries(data.globalState.repositories).map(([key, value]) =>
					key === oldName ? [newName, value] : [key, value]
				)
			);
			saveState(data.globalState);
		}
	};

	const openEditRepo = (name: string, url: string, apiKeySecret: string | null) => {
		editRepoName = name;
		editRepoUrl = url;
		editRepoSecret = apiKeySecret;
		editModalOpen = true;
	};
</script>

<Page title={$t('nav.external-repositories')} subtitle={$t('settings.repo.subtitle')}>
	{#snippet actions()}
		<CreateButton label={$t('settings.repo.add')} onclick={() => addRepo()} />
	{/snippet}
	<EditExternalRepoUrl
		bind:open={editModalOpen}
		inputName={editRepoName}
		inputUrl={editRepoUrl}
		apiSecret={editRepoSecret}
		secrets={Object.values(data.secrets)}
		isNew={creatingRepo}
		onSecretChange={(secretId) => {
			editRepoSecret = secretId;
			if (!creatingRepo && editRepoName && editRepoName in data.globalState.repositories) {
				data.globalState.repositories[editRepoName].api_key_secret = secretId;
				saveState(data.globalState);
			}
		}}
		onSave={(newUrl) => {
			if (creatingRepo && editRepoName) {
				data.globalState.repositories = {
					...data.globalState.repositories,
					[editRepoName]: { url: newUrl, api_key_secret: editRepoSecret ?? null }
				};
				saveState(data.globalState);
			} else if (editRepoName && editRepoName in data.globalState.repositories) {
				data.globalState.repositories[editRepoName].url = newUrl;
				saveState(data.globalState);
			}
		}}
		onRename={(newName) => {
			if (editRepoName) changeRepoName(editRepoName, newName);
		}}
		onClose={() => {
			editRepoName = undefined;
			editRepoUrl = undefined;
			editRepoSecret = undefined;
			creatingRepo = false;
		}}
	/>
	<DetailsModal
		bind:open={detailsModalOpen}
		title={$t('settings.repo.show-details-title')}
		details={detailsText}
	/>
	<DeleteConfirm
		target={deleteRepoConfirm}
		on:confirm={() => {
			if (deleteRepoConfirm) deleteRepo(deleteRepoConfirm);
		}}
		on:cancel={() => {
			deleteRepoConfirm = undefined;
		}}
	/>
	<Modal bind:open={testConnectionOpen} size="lg" title={$t('settings.repo.check')}>
		<RepoConnectionTest inputUrl={testConnectionInput} apiSecret={testConnectionApiSecret} />
	</Modal>
	<DataTable
		columns={[
			{ label: $t('settings.repo.name') },
			{ label: $t('settings.repo.url') },
			{ label: $t('settings.repo.status') },
			{ label: $t('settings.repo.actions'), align: 'right' }
		]}
		rows={Object.entries(data.globalState.repositories)}
		empty={$t('settings.repo.empty')}
	>
		{#snippet row([name, repo])}
			{@const status = data.externalRepositoriesStatus[name]}
			<td>
				<button
					class="ds-name-btn"
					onclick={() => openEditRepo(name, repo.url, repo.api_key_secret)}
					title={$t('settings.repo.edit')}
				>
					{name}
				</button>
			</td>
			<td>{repo.url}</td>
			<td class="min-w-48">
				<div class="flex flex-col items-start gap-1.5">
					{#if status?.status === 'loading'}
						<span class="ds-status-pill offline">
							<Spinner size="3" />
							{$t('settings.repo-status.loading')}
						</span>
					{:else if status?.status === 'no-path'}
						<span class="ds-status-pill danger">
							<span class="ds-dot"></span>{$t('settings.repo-status.no-path')}
						</span>
					{:else if status?.status === 'no-readme'}
						<span class="ds-status-pill warning">
							<span class="ds-dot"></span>{$t('settings.repo-status.no-readme')}
						</span>
					{:else if status?.status === 'no-magic-string'}
						<span class="ds-status-pill warning">
							<span class="ds-dot"></span>{$t('settings.repo-status.no-magic-string')}
						</span>
					{:else if status?.status === 'loaded'}
						<span class="ds-status-pill online">
							<span class="ds-dot"></span>
							{$t('settings.repo-status.loaded', { values: { count: status.modules.length } })}
						</span>
						{#if status.modules.length}
							<div class="flex flex-wrap gap-1">
								{#each status.modules as module_id}
									{@const module = data.globalState.availableModules.find(
										(m) => m.type === module_id
									)}
									<span class="ds-tag flex items-center gap-1">
										{#if module}
											<ModuleIcon {module} imageClass="m-0 w-4" />
										{/if}
										{module?.displayName || module_id}
									</span>
								{/each}
							</div>
						{/if}
					{:else}
						<span style="color: var(--ds-text-mute)">—</span>
					{/if}
					{#if status?.details}
						<button
							class="ds-btn ds-btn-sm"
							onclick={() => {
								detailsModalOpen = true;
								detailsText = status.details;
							}}
						>
							{$t('settings.repo.show-details')}
						</button>
					{/if}
				</div>
			</td>
			<td>
				<RowActions>
					<RowMenu
						label={$t('settings.repo.actions')}
						items={[
							{
								label: $t('settings.repo.edit'),
								icon: Pen,
								onclick: () => openEditRepo(name, repo.url, repo.api_key_secret)
							},
							{
								label: $t('settings.repo.check'),
								icon: RefreshCw,
								onclick: () => {
									testConnectionInput = repo.url;
									testConnectionApiSecret = repo.api_key_secret;
									testConnectionOpen = true;
								}
							},
							{
								label: $t('settings.repo.delete'),
								icon: Trash,
								variant: 'danger',
								onclick: () => (deleteRepoConfirm = name)
							}
						]}
					/>
				</RowActions>
			</td>
		{/snippet}
	</DataTable>
</Page>
