<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { saveState } from '$lib/state';
	import EditStringModal from '$lib/EditStringModal.svelte';
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
	import Pen from 'lucide-svelte/icons/pen';

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

	enum ModalType {
		None,
		EditRepoName,
		EditRepoUrl
	}

	let openModal = ModalType.None;
	let editRepo: string | undefined;

	const openEditRepoNameModal = (name: string) => {
		editRepo = name;
		openModal = ModalType.EditRepoName;
	};

	const closeEditNameModal = () => {
		openModal = ModalType.None;
	};

	const saveEditNameModal = (value: string) => {
		if (editRepo && value !== editRepo && !data.state.repositories[value]) {
			data.state.repositories = {
				...data.state.repositories,
				[value]: data.state.repositories[editRepo]
			};
			delete data.state.repositories[editRepo];
		}

		closeEditNameModal();
		saveState(data.state);
	};

	const openEditRepoUrlModal = (name: string) => {
		editRepo = name;
		openModal = ModalType.EditRepoUrl;
	};

	const closeEditUrlModal = () => {
		openModal = ModalType.None;
	};

	const saveEditUrlModal = (value: string) => {
		if (editRepo) {
			data.state.repositories = {
				...data.state.repositories,
				[editRepo]: {
					...data.state.repositories[editRepo],
					url: value
				}
			};
		}

		closeEditUrlModal();
		saveState(data.state);
	};
</script>

<EditStringModal
	title={$t('settings.repo.edit-name')}
	value={editRepo}
	open={openModal === ModalType.EditRepoName}
	onClose={closeEditNameModal}
	onSave={saveEditNameModal}
/>

<EditStringModal
	title={$t('settings.repo.edit-url')}
	value={editRepo ? data.state.repositories[editRepo]?.url : ''}
	open={openModal === ModalType.EditRepoUrl}
	onClose={closeEditUrlModal}
	onSave={saveEditUrlModal}
/>

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
				<TableBodyCell>
					<div class="flex gap-1">
						{name}
						<button class="btn ml-2 p-0" on:click={() => openEditRepoNameModal(name)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
				<TableBodyCell>
					<div class="flex gap-1">
						{repo.url}
						<button class="btn ml-2 p-0" on:click={() => openEditRepoUrlModal(name)}>
							<Pen size="20" />
						</button>
					</div>
				</TableBodyCell>
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
