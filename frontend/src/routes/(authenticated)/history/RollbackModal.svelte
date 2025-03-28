<script lang="ts">
	import { t } from 'svelte-i18n';
	import { invalidate } from '$app/navigation';
	import { Button, Modal } from 'flowbite-svelte';
	import type { Commit } from '$lib/history';
	import { fetchWithNotify } from '$lib/fetchWithNotify';

	interface Props {
		commit: Commit | undefined;
	}

	let { commit = $bindable() }: Props = $props();

	const revertCommit = async (commitSHA: string | undefined) => {
		if (commitSHA === undefined) return;

		await fetchWithNotify(`/api/history/revert-commit?commit_sha=${commitSHA}`, { method: 'POST' });
		await invalidate((url) => url.pathname === '/api/history' || url.pathname === '/api/state');

		commit = undefined;
	};
</script>

<Modal
	open={commit !== undefined}
	on:close={() => (commit = undefined)}
	title={$t('history.rollback-modal-title')}
>
	<p class="whitespace-pre-wrap">
		{$t('history.rollback-modal-body', {
			values: { newCommit: commit?.SHA1 + ': ' + commit?.message }
		})}
	</p>
	{#snippet footer()}
		<div class="flex justify-between w-full">
			<Button color="alternative" on:click={() => (commit = undefined)}>
				{$t('common.cancel')}
			</Button>
			<Button on:click={() => revertCommit(commit?.SHA1)}>
				{$t('history.rollback-modal-confirm')}
			</Button>
		</div>
	{/snippet}
</Modal>
