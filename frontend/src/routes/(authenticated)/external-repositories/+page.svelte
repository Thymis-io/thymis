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
		TableBodyCell
	} from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

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
				url: 'git+https://github.com/Thymis-io/thymis.git'
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
		<TableHeadCell padding="p-2">{$t('settings.repo.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each Object.entries(data.globalState.repositories) as [name, repo]}
			<TableBodyRow>
				<TableBodyEditCell value={name} onEnter={(newName) => changeRepoName(name, newName)} />
				<TableBodyEditCell bind:value={repo.url} onEnter={() => saveState(data.globalState)} />
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
