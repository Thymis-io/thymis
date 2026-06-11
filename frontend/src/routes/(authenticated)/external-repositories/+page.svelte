<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState } from '$lib/state';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import { Modal, Spinner } from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import SecretSelect from '$lib/components/secrets/SecretSelect.svelte';
	import Pen from 'lucide-svelte/icons/pen';
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

	const addRepo = () => {
		let key = generateUniqueKey();

		data.globalState.repositories = {
			...data.globalState.repositories,
			[key]: {
				url: 'git+https://github.com/Thymis-io/thymis.git',
				api_key_secret: null
			}
		};

		saveState(data.globalState);
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
</script>

<EditExternalRepoUrl
	bind:open={editModalOpen}
	inputName={editRepoName}
	inputUrl={editRepoUrl}
	apiSecret={editRepoSecret}
	onSave={(newUrl) => {
		if (editRepoName && editRepoName in data.globalState.repositories) {
			data.globalState.repositories[editRepoName].url = newUrl;
			saveState(data.globalState);
		}
	}}
	onClose={() => {
		editRepoName = undefined;
		editRepoUrl = undefined;
		editRepoSecret = undefined;
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
<PageHead
	title={$t('nav.external-repositories')}
	subtitle={$t('settings.repo.subtitle')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
>
	{#snippet actions()}
		<button class="ds-btn ds-btn-primary whitespace-nowrap" onclick={() => addRepo()}>
			+ {$t('settings.repo.add')}
		</button>
	{/snippet}
</PageHead>
<div class="ds-table-wrap">
	<table class="ds-table">
		<thead>
			<tr>
				<th>{$t('settings.repo.name')}</th>
				<th>{$t('settings.repo.url')}</th>
				<th>{$t('settings.repo.secret')}</th>
				<th>{$t('settings.repo.status')}</th>
				<th class="text-right">{$t('settings.repo.actions')}</th>
			</tr>
		</thead>
		<tbody>
			{#each Object.entries(data.globalState.repositories) as [name, repo]}
				{@const status = data.externalRepositoriesStatus[name]}
				<tr>
					<TableBodyEditCell value={name} onEnter={(newName) => changeRepoName(name, newName)} />
					<td>
						<div class="flex items-center gap-3">
							<span>{repo.url}</span>
							<button
								class="shrink-0"
								style="color: var(--ds-text-mute)"
								onclick={() => {
									editRepoName = name;
									editRepoUrl = repo.url;
									editRepoSecret = repo.api_key_secret;
									editModalOpen = true;
								}}
							>
								<Pen size={'0.875rem'} class="min-w-4" />
							</button>
						</div>
					</td>
					<td class="min-w-48 pr-2 xl:pr-12">
						<SecretSelect
							secret={repo.api_key_secret ? data.secrets[repo.api_key_secret] : undefined}
							onChange={(secret) => {
								repo.api_key_secret = secret?.id || null;
								saveState(data.globalState);
							}}
							allowedTypes={['single_line']}
							secrets={Object.values(data.secrets)}
						/>
					</td>
					<td class="min-w-48 text-xs">
						{#if status?.status === 'loading'}
							<div class="flex items-center gap-2">
								<Spinner size="4" />
								{$t('settings.repo-status.loading')}
							</div>
						{:else if status?.status === 'no-path'}
							{$t('settings.repo-status.no-path')}
						{:else if status?.status === 'no-readme'}
							{$t('settings.repo-status.no-readme')}
						{:else if status?.status === 'no-magic-string'}
							{$t('settings.repo-status.no-magic-string')}
						{:else if status?.status === 'loaded'}
							{$t('settings.repo-status.loaded', { values: { count: status.modules.length } })}
							{#each status.modules as module_id}
								{@const module = data.globalState.availableModules.find(
									(m) => m.type === module_id
								)}
								<div class="flex items-center gap-1">
									{#if module}
										<ModuleIcon {module} imageClass="w-5 m-0.5" />
									{/if}
									{module?.displayName || module_id}
								</div>
							{/each}
						{/if}
						{#if status?.details}
							<button
								class="ds-btn ds-btn-sm ml-2"
								onclick={() => {
									detailsModalOpen = true;
									detailsText = status.details;
								}}
							>
								{$t('settings.repo.show-details')}
							</button>
						{/if}
					</td>
					<td>
						<div class="flex justify-end gap-2">
							<button
								class="ds-btn ds-btn-sm"
								onclick={() => {
									testConnectionInput = repo.url;
									testConnectionApiSecret = repo.api_key_secret;
									testConnectionOpen = true;
								}}
							>
								{$t('settings.repo.check')}
							</button>
							<button
								class="ds-btn ds-btn-sm ds-btn-danger"
								onclick={() => (deleteRepoConfirm = name)}
							>
								{$t('settings.repo.delete')}
							</button>
						</div>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
