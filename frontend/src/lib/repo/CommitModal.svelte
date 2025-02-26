<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import { type RepoStatus } from '$lib/repo/repo';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { invalidate } from '$app/navigation';
	import FileChanges from './FileChanges.svelte';

	export let repoStatus: RepoStatus;

	let message = 'commit';
	let selectedFile = '';
	$: hasFileChanges = repoStatus.changes.length > 0;

	export let open = false;

	const commit = async () => {
		await fetchWithNotify(`/api/action/commit?message=${encodeURIComponent(message)}`, {
			method: 'POST'
		});
		await invalidate(
			(url) => url.pathname === '/api/history' || url.pathname === '/api/repo_status'
		);

		message = '';
		open = false;
	};
</script>

<Modal
	bind:open
	title={$t('deploy.commit')}
	size="xl"
	outsideclose
	on:open={() => {
		selectedFile = 'state.json';
	}}
>
	<div class={'flex flex-col gap-8 ' + (hasFileChanges ? 'h-[60vh]' : '')}>
		{#if hasFileChanges}
			<div>
				<p class="text-base text-gray-900 dark:text-white mb-1">{$t('deploy.summary')}</p>
				<Input
					type="text"
					bind:value={message}
					placeholder={$t('deploy.summary')}
					disabled={repoStatus.changes.length === 0}
				/>
			</div>
			<p class="text-base text-gray-900 dark:text-white mb-[-2em]">{$t('deploy.open-changes')}</p>
			<FileChanges {repoStatus} {selectedFile} />
		{:else}
			<p class="text-base text-gray-900 dark:text-white">{$t('deploy.no-changes')}</p>
		{/if}
		<div class="flex justify-end">
			<Button
				on:click={commit}
				disabled={repoStatus.changes.length === 0 || message.length === 0}
				class="w-48"
			>
				{$t('deploy.commit')}
			</Button>
		</div>
	</div>
</Modal>
