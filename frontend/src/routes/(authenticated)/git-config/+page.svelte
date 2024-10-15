<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import Pen from 'lucide-svelte/icons/pen';
	import Trash from 'lucide-svelte/icons/trash';
	import {
		Button,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import type { Remote } from '$lib/history';
	import RemoteModal from './RemoteModal.svelte';
	import { invalidate } from '$app/navigation';

	export let data: PageData;

	let editRemote: Remote | undefined;
	let createRemote: boolean = false;
	let originalEditRemoteName: string | undefined;

	const deleteRemote = async (name: string) => {
		await fetch(`/api/git/remote/${name}`, {
			method: 'DELETE'
		});

		invalidate((url) => url.pathname === '/api/git/info');
	};
</script>

<RemoteModal
	remote={editRemote}
	originalName={originalEditRemoteName}
	create={createRemote}
	remotes={data.gitInfo.remotes}
/>
<p>On branch {data.gitInfo.active_branch}, following {data.gitInfo.remote_branch}</p>
<p class="mt-4">{$t('git-config.remotes-title')}</p>
<Table shadow>
	<TableHead>
		<TableHeadCell padding="py-2 px-4">{$t('git-config.remotes.name')}</TableHeadCell>
		<TableHeadCell padding="py-2 px-4">{$t('git-config.remotes.url')}</TableHeadCell>
		<TableHeadCell padding="py-2 px-4">{$t('git-config.remotes.actions')}</TableHeadCell>
	</TableHead>
	<TableBody>
		{#each data.gitInfo.remotes as remote}
			<TableBodyRow>
				<TableBodyCell tdClass="p-2 px-2 md:px-4">{remote.name}</TableBodyCell>
				<TableBodyCell tdClass="p-2 px-2 md:px-4">{remote.url}</TableBodyCell>
				<TableBodyCell tdClass="p-2 px-2 md:px-4" class="flex gap-2">
					<Button
						size="sm"
						class="flex gap-2"
						color="alternative"
						on:click={() => {
							editRemote = { ...remote };
							originalEditRemoteName = remote.name;
							createRemote = false;
						}}
					>
						<Pen size={18} />
						{$t('git-config.edit-remote')}
					</Button>
					<Button
						size="sm"
						class="flex gap-2 ml-8"
						color="alternative"
						on:click={() => deleteRemote(remote.name)}
					>
						<Trash size={18} />
						{$t('git-config.delete-remote')}
					</Button>
				</TableBodyCell>
			</TableBodyRow>
		{/each}
	</TableBody>
</Table>
<Button
	color="alternative"
	class="mt-4"
	on:click={() => {
		editRemote = { name: '', url: '' };
		createRemote = true;
	}}
>
	+
</Button>
