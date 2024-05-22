<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { saveState } from '$lib/state';
	import TableBodyEditCell from '$lib/TableBodyEditCell.svelte';
	import {
		Button,
		Heading,
		P,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell
	} from 'flowbite-svelte';

	export let data: PageData;

	const addRepo = () => {
		let num = 1;
		let key;

		do {
			key = `new-repo-${num}`;
			num++;
		} while (data.state.repositories[key]);

		data.state.repositories = {
			...data.state.repositories,
			[key]: {
				url: 'git+https://github.com/Thymis-io/thymis.git'
			}
		};

		saveState(data.state);
	};

	const deleteRepo = (name: string) => {
		delete data.state.repositories[name];
		saveState(data.state);
	};

	const changeRepoName = (oldName: string, newName: string) => {
		if (!data.state.repositories[newName]) {
			data.state.repositories = Object.fromEntries(
				Object.entries(data.state.repositories).map(([key, value]) =>
					key === oldName ? [newName, value] : [key, value]
				)
			);
		}

		saveState(data.state);
	};
</script>

<Heading tag="h3">{$t('nav.settings')}</Heading>
<Heading tag="h4" class="mt-4">{$t('settings.repo.title')}</Heading>
<Table class="mt-4">
	<TableHead>
		<TableHeadCell>{$t('settings.repo.name')}</TableHeadCell>
		<TableHeadCell>{$t('settings.repo.url')}</TableHeadCell>
		<TableHeadCell>{$t('settings.repo.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each Object.entries(data.state.repositories) as [name, repo]}
			<TableBodyRow>
				<TableBodyEditCell bind:value={name} onEnter={(newName) => changeRepoName(name, newName)} />
				<TableBodyEditCell bind:value={repo.url} onEnter={() => saveState(data.state)} />
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
