<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState, type Repo } from '$lib/state';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import {
		Button,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell,
		Spinner
	} from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';
	import SecretSelect from '$lib/components/secrets/SecretSelect.svelte';
	import Check from 'lucide-svelte/icons/check';
	import Hourglass from 'lucide-svelte/icons/hourglass';
	import X from 'lucide-svelte/icons/x';
	import Pen from 'lucide-svelte/icons/pen';
	import EditExternalRepoUrl from '$lib/components/EditExternalRepoUrl.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let editModalOpen = $state(false);
	let editRepoName = $state<string>();

	let externalRepoStatus = $state<
		Record<
			string,
			| { status: 'pending' }
			| { status: 'success' }
			| { status: 'error'; detail: string }
			| { status: 'unknown' }
			| { status: 'rate_limited' }
		>
	>({});

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

	const checkRepoStatus = async (name: string) => {
		externalRepoStatus[name] = { status: 'pending' };
		const result = await (await fetch(`/api/external-repositories/test-flake-ref/${name}`)).json();
		if (result.status === 'success') {
			externalRepoStatus[name] = { status: 'success' };
		} else if (result.status === 'rate_limited') {
			externalRepoStatus[name] = { status: 'rate_limited' };
		} else if (result.status === 'error') {
			externalRepoStatus[name] = { status: 'error', detail: result.detail };
		} else {
			externalRepoStatus[name] = { status: 'unknown' };
		}
	};
</script>

<EditExternalRepoUrl
	bind:open={editModalOpen}
	inputName={editRepoName}
	onSave={(newUrl) => {
		if (editRepoName && editRepoName in data.globalState.repositories) {
			data.globalState.repositories[editRepoName].url = newUrl;
			saveState(data.globalState);
		}
	}}
/>
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
								editModalOpen = true;
							}}
						>
							<Pen size={'1rem'} class="min-w-4" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
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
				<TableBodyCell tdClass="p-2">
					<Button
						class="flex gap-1"
						on:click={() => checkRepoStatus(name)}
						disabled={externalRepoStatus[name]?.status === 'pending'}
					>
						{#if externalRepoStatus[name]?.status === 'pending'}
							<Spinner size="4" />
							{$t('settings.repo.check')}
						{:else if externalRepoStatus[name]?.status === 'success'}
							<Check class="text-green-500" size="20" />
							{$t('settings.repo.check-success')}
						{:else if externalRepoStatus[name]?.status === 'rate_limited'}
							<Hourglass class="text-yellow-500" size="20" />
							{$t('settings.repo.check-rate-limited')}
						{:else if externalRepoStatus[name]?.status === 'error'}
							<X class="text-red-500" size="20" />
							{$t('settings.repo.check-error')}:
							{externalRepoStatus[name]?.detail}
						{:else}
							{$t('settings.repo.check')}
						{/if}
					</Button>
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{@const status = data.externalRepositoriesStatus[name]}
					{#if status}
						{status.status}:
						{status.modules.length}
						{#each status.modules as module}
							<div>{module}</div>
						{/each}
						<span class="whitespace-pre">{status.details}</span>
					{/if}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<div class="flex gap-1">
						<Button on:click={() => deleteRepo(name)}>
							{$t('settings.repo.delete')}
						</Button>
					</div>
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<Button color="alternative" class="mt-4" on:click={() => addRepo()}>+</Button>
