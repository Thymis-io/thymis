<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import Pen from 'lucide-svelte/icons/pen';
	import Trash from 'lucide-svelte/icons/trash';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import ExternalLink from 'lucide-svelte/icons/external-link';
	import Warning from 'lucide-svelte/icons/triangle-alert';
	import {
		Button,
		Dropdown,
		DropdownItem,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell,
		Tooltip,
		Spinner
	} from 'flowbite-svelte';
	import type { Remote, EditRemote } from '$lib/history';
	import RemoteModal from './RemoteModal.svelte';
	import { invalidate } from '$app/navigation';
	import ConfirmSwitchModal from './ConfirmSwitchModal.svelte';

	export let data: PageData;

	let editRemote: EditRemote | undefined;
	let createRemote: boolean = false;
	let originalEditRemoteName: string | undefined;

	let switchBranch: string | undefined = undefined;
	let switchingRemoteBranch = false;

	const deleteRemote = async (name: string) => {
		await fetch(`/api/git/remote/${name}`, {
			method: 'DELETE'
		});

		invalidate((url) => url.pathname === '/api/git/info');
	};

	const switchRemoteBranch = async (branch: string) => {
		switchingRemoteBranch = true;
		await fetch(`/api/git/switch-remote-branch/${encodeURIComponent(branch)}`, {
			method: 'PATCH'
		});

		await invalidate((url) => url.pathname === '/api/git/info');
		switchingRemoteBranch = false;
	};

	$: remote = data.gitInfo.remotes.find(
		(r) => data.gitInfo.remote_branch && r.branches.includes(data.gitInfo.remote_branch)
	);

	const guessRemoteHttpUrl = (remote: Remote | undefined, remoteBranch: string | undefined) => {
		const remoteUrl = remote?.url;

		if (!remoteUrl) {
			return;
		}

		let baseUrl = '';

		if (remoteUrl.startsWith('http')) {
			baseUrl = remoteUrl.replace(/\.git$/, '');
		} else if (new RegExp(/.*@.*:/).test(remoteUrl)) {
			baseUrl = `https://${remoteUrl
				.replace(/.*@/, '')
				.replace(/:/, '/')
				.replace(/\.git$/, '')}`;
		}

		if (baseUrl) {
			return baseUrl + '/tree/' + remoteBranch?.replace(`${remote.name}/`, '');
		}
	};
</script>

<RemoteModal
	remote={editRemote}
	originalName={originalEditRemoteName}
	create={createRemote}
	remotes={data.gitInfo.remotes}
/>
<ConfirmSwitchModal
	currentBranch={data.gitInfo.remote_branch ?? undefined}
	remoteBranch={switchBranch}
	on:confirm={() => switchBranch && switchRemoteBranch(switchBranch)}
	on:cancel={() => (switchBranch = undefined)}
/>
<div class="flex flex-row gap-2 items-center">
	{#if data.gitInfo.remote_branch && data.gitInfo.ahead === 0 && data.gitInfo.ahead === 0}
		<span>{$t('git-config.remote-info')}</span>
	{:else if data.gitInfo.remote_branch}
		<Warning color="yellow" />
		<span>{$t('git-config.remote-info-out-of-sync')}</span>
	{:else}
		<span>{$t('git-config.no-remote-info')}</span>
	{/if}
	{#if switchingRemoteBranch}
		<Spinner size={5} />
	{:else}
		<button class="flex flex-row gap-1 items-center"
			>{data.gitInfo.remote_branch ?? '-'} <ChevronDown size={20} /></button
		>
		<Dropdown>
			{#each data.gitInfo.remotes as remote}
				{#each remote.branches as branch}
					{@const isRemoteBranch = data.gitInfo.remote_branch === branch}
					<DropdownItem
						on:click={() => (switchBranch = branch)}
						class={`${isRemoteBranch ? 'text-primary-500' : ''}`}>{branch}</DropdownItem
					>
				{/each}
			{/each}
		</Dropdown>
		{#if guessRemoteHttpUrl(remote, data.gitInfo.remote_branch ?? undefined)}
			<a
				href={guessRemoteHttpUrl(remote, data.gitInfo.remote_branch ?? undefined)}
				target="_blank"
				rel="noopener noreferrer"
			>
				<ExternalLink size={20} />
			</a>
			<Tooltip placement="top" class="z-50">{$t('git-config.external-repo-link')}</Tooltip>
		{/if}
	{/if}
</div>
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
