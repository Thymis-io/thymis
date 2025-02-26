<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import { type RepoStatus } from '$lib/repo/repo';
	import FileChanges from './FileChanges.svelte';

	export let repoStatus: RepoStatus;
	export let title: string | undefined = undefined;
	export let action: string | undefined = undefined;
	export let defaultMessage: string = 'commit';

	let message = defaultMessage;
	let selectedFile = '';
	$: hasFileChanges = repoStatus.changes.length > 0;

	export let open = false;

	export let onAction: (message: string) => void;
</script>

<Modal
	bind:open
	title={title ?? $t('deploy.commit')}
	size="xl"
	outsideclose
	on:open={() => {
		selectedFile = 'state.json';
		message = defaultMessage;
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
				on:click={() => {
					onAction(message);
					message = defaultMessage;
					open = false;
				}}
				disabled={repoStatus.changes.length === 0 || message.length === 0}
				class="w-48"
			>
				{action ?? $t('deploy.commit')}
			</Button>
		</div>
	</div>
</Modal>
