<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import { type RepoStatus } from '$lib/repo/repo';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { invalidate } from '$app/navigation';
	import FileChanges from './FileChanges.svelte';

	export let repoStatus: RepoStatus;

	let message = '';
	let selectedFile = '';

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
	<div class="flex flex-col h-[80vh]">
		<div>
			<p class="text-base text-gray-900 dark:text-white mb-1">{$t('deploy.summary')}</p>
			<div class="flex flex-row gap-2">
				<Input type="text" bind:value={message} placeholder={$t('deploy.summary')} />
				<Button
					on:click={commit}
					disabled={repoStatus.changes.length === 0 || message.length === 0}
				>
					{$t('deploy.commit')}
				</Button>
			</div>
		</div>
		<FileChanges {repoStatus} {selectedFile} />
	</div>
</Modal>
