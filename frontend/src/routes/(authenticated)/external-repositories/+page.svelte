<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from '../settings/$types';
	import { saveState, state } from '$lib/state';
	import TableBodyEditCell from '$lib/components/TableBodyEditCell.svelte';
	import {
		Button,
		Heading,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell
	} from 'flowbite-svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';

	export let data: PageData;

	const generateUniqueKey = () => {
		let num = 1;
		let key;

		do {
			key = `new-repo-${num}`;
			num++;
		} while ($state.repositories[key]);

		return key;
	};

	const addRepo = () => {
		let key = generateUniqueKey();

		$state.repositories = {
			...$state.repositories,
			[key]: {
				url: 'git+https://github.com/Thymis-io/thymis.git'
			}
		};

		saveState();
	};

	const deleteRepo = (name: string) => {
		$state.repositories = Object.fromEntries(
			Object.entries($state.repositories).filter(([key, value]) => key !== name)
		);

		saveState();
	};

	const changeRepoName = (oldName: string, newName: string) => {
		if (!$state.repositories[newName]) {
			$state.repositories = Object.fromEntries(
				Object.entries($state.repositories).map(([key, value]) =>
					key === oldName ? [newName, value] : [key, value]
				)
			);
			saveState();
		}
	};
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">{$t('nav.external-repositories')}</h1>
	<DeployActions />
</div>
<Table shadow>
	<TableHead>
		<TableHeadCell>{$t('settings.repo.name')}</TableHeadCell>
		<TableHeadCell>{$t('settings.repo.url')}</TableHeadCell>
		<TableHeadCell>{$t('settings.repo.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each Object.entries($state.repositories) as [name, repo]}
			<TableBodyRow>
				<TableBodyEditCell bind:value={name} onEnter={(newName) => changeRepoName(name, newName)} />
				<TableBodyEditCell bind:value={repo.url} onEnter={() => saveState()} />
				<TableBodyCell>
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
