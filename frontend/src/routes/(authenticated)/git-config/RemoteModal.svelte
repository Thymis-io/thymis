<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type Device, saveState, state, type Tag } from '$lib/state';
	import { Button, Modal, Label, P, Input, Helper } from 'flowbite-svelte';
	import type { Remote } from '$lib/history';
	import { invalidate } from '$app/navigation';

	export let remote: Remote | undefined;
	export let originalName: string | undefined;
	export let create: boolean = false;
	export let remotes: Remote[];

	const saveRemote = async (remote: Remote) => {
		if (create) {
			await fetch('/api/git/remote', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(remote)
			});
		} else {
			await fetch(`/api/git/remote/${originalName}`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(remote)
			});
		}

		invalidate((url) => url.pathname === '/api/git/info');
	};

	const existsRemote = (name: string) => {
		return !!remotes.find((r) => remote && r.name === name && r.name !== originalName);
	};
</script>

{#if remote}
	<Modal
		title={create
			? $t('git-config.create-remote-modal-title')
			: $t('git-config.edit-remote-modal-title')}
		open={!!remote}
		on:close={() => (remote = undefined)}
		outsideclose
		bodyClass="p-4 md:p-5 space-y-4 flex-1"
	>
		<form>
			<div class="mb-4">
				<Label for="remote-name">{$t('git-config.remote-name')}</Label>
				<Input id="remote-name" bind:value={remote.name} />
				{#if remote.name === ''}
					<Helper color="red">{$t('git-config.remote-name-required')}</Helper>
				{:else if existsRemote(remote.name)}
					<Helper color="red">{$t('git-config.remote-name-exists')}</Helper>
				{/if}
			</div>
			<div class="mb-4">
				<Label for="remote-url">{$t('git-config.remote-url')}</Label>
				<Input id="remote-url" bind:value={remote.url} />
				{#if remote.url === ''}
					<Helper color="red">{$t('git-config.remote-url-required')}</Helper>
				{/if}
			</div>
			<div class="flex justify-end gap-2">
				<Button
					color="alternative"
					on:click={() => {
						remote = undefined;
					}}
				>
					{$t('common.cancel')}
				</Button>
				<Button
					on:click={() => {
						if (remote) saveRemote(remote);
						remote = undefined;
					}}
					disabled={remote.name === '' || remote.url === '' || existsRemote(remote.name)}
				>
					{$t('common.save')}
				</Button>
			</div>
		</form>
	</Modal>F
{/if}
