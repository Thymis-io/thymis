<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState, state } from '$lib/state';
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
	import ArrowRightFromLine from 'lucide-svelte/icons/arrow-right-from-line';
	import Import from 'lucide-svelte/icons/import';
	import PageHead from '$lib/components/PageHead.svelte';

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

<!-- <PageHead title={$t('nav.external-repositories')} /> -->
<PageHead title={$t('nav.project-settings')} />

<h2 class="text-2xl font-bold">{$t('nav.backup-export-import')}</h2>

<!--
Backuping:
The user is supposed to:
- Click on the "Backup/Export project" button
- The frontend will send a request to the backend to create a backup of the project
- The backend will create a backup of the project and return the backup file
- The frontend will download the backup file

Importing:
The user is supposed to:
- Click on the "Import project" button
- The user will be prompted to select a backup file
- The frontend will send the backup file to the backend
- The backend will show information about the backup file and ask the user to confirm the import
- The frontend will send a request to the backend to import the project
- The backend will import the project and restart the server
-->

<p>
	{$t('settings.backup-export-import-description')}
</p>

<div class="flex gap-4 mt-4">
	<Button class="" on:click={async () => {}}>
		<ArrowRightFromLine size="1rem" class="min-w-4 mr-2" />
		{$t('settings.backup-export')}</Button
	>
	<Button
		class=""
		on:click={() => {
			// todo: implement import
		}}
	>
		<Import size="1rem" class="min-w-4 mr-2" />
		{$t('settings.import-project')}</Button
	>
</div>

<h2 class="mt-6 text-2xl font-bold">{$t('nav.external-repositories')}</h2>
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2">{$t('settings.repo.name')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('settings.repo.url')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('settings.repo.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each Object.entries($state.repositories) as [name, repo]}
			<TableBodyRow>
				<TableBodyEditCell bind:value={name} onEnter={(newName) => changeRepoName(name, newName)} />
				<TableBodyEditCell bind:value={repo.url} onEnter={() => saveState()} />
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
