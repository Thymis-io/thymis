<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState } from '$lib/state';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import {
		Button,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell,
		Modal
	} from 'flowbite-svelte';
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
	apiSecret={editRepoSecret}
	onSave={(newUrl) => {
		if (editRepoName && editRepoName in data.globalState.repositories) {
			data.globalState.repositories[editRepoName].url = newUrl;
			saveState(data.globalState);
		}
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
/>
<Modal bind:open={testConnectionOpen} size="lg" title={$t('settings.repo.check')}>
	<RepoConnectionTest inputUrl={testConnectionInput} apiSecret={testConnectionApiSecret} />
</Modal>
<PageHead
	title={$t('nav.external-repositories')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2">{$t('settings.repo.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('settings.repo.url')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('settings.repo.secret')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('settings.repo.status')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('settings.repo.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each Object.entries(data.globalState.repositories) as [name, repo]}
			<TableBodyRow>
				<TableBodyEditCell value={name} onEnter={(newName) => changeRepoName(name, newName)} />
				<TableBodyCell tdClass="p-2 px-2 md:px-4">
					<div class="flex gap-4 p-0">
						<span class="p-0">{repo.url}</span>
						<button
							onclick={() => {
								editRepoName = name;
								editRepoSecret = repo.api_key_secret;
								editModalOpen = true;
							}}
						>
							<Pen size={'1rem'} class="min-w-4" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell tdClass="p-2 min-w-48 pr-2 xl:pr-12">
					<SecretSelect
						secret={repo.api_key_secret ? data.secrets[repo.api_key_secret] : undefined}
						onChange={(secret) => {
							repo.api_key_secret = secret?.id || null;
							saveState(data.globalState);
						}}
						allowedTypes={['single_line']}
						secrets={Object.values(data.secrets)}
					/>
				</TableBodyCell>
				<TableBodyCell tdClass="p-2 min-w-48 text-xs">
					{@const status = data.externalRepositoriesStatus[name]}
					{#if status.status === 'no-path'}
						{$t('settings.repo-status.no-path')}
					{:else if status.status === 'no-readme'}
						{$t('settings.repo-status.no-readme')}
					{:else if status.status === 'no-magic-string'}
						{$t('settings.repo-status.no-magic-string')}
					{:else if status.status === 'loaded'}
						{$t('settings.repo-status.loaded', { values: { count: status.modules.length } })}
						{#each status.modules as module_id}
							{@const module = data.globalState.availableModules.find((m) => m.type === module_id)}
							<div class="flex items-center gap-1">
								{#if module}
									<ModuleIcon {module} imageClass="w-5 m-0.5" />
								{/if}
								{module?.displayName || module_id}
							</div>
						{/each}
					{/if}
					{#if status.details}
						<Button
							size="xs"
							color="alternative"
							class="ml-2"
							on:click={() => {
								detailsModalOpen = true;
								detailsText = status.details;
							}}
						>
							{$t('settings.repo.show-details')}
						</Button>
					{/if}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2 flex gap-2">
					<Button
						class="flex gap-1"
						on:click={() => {
							testConnectionInput = repo.url;
							testConnectionApiSecret = repo.api_key_secret;
							testConnectionOpen = true;
						}}
					>
						{$t('settings.repo.check')}
					</Button>
					<div class="flex gap-1">
						<Button on:click={() => (deleteRepoConfirm = name)}>
							{$t('settings.repo.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<Button color="alternative" class="mt-4" on:click={() => addRepo()}>+</Button>
