<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import { type RepoStatus } from '$lib/repo/repo';
	import FileChanges from './FileChanges.svelte';

	interface Props {
		repoStatus: RepoStatus;
		title?: string | undefined;
		action?: string | undefined;
		defaultMessage?: string;
		open?: boolean;
		onAction: (message: string) => Promise<void> | void;
	}

	let {
		repoStatus,
		title = undefined,
		action = undefined,
		defaultMessage = 'commit',
		open = $bindable(false),
		onAction
	}: Props = $props();

	let hasFileChanges = $derived(repoStatus.changes.length > 0);
	let message = $state(defaultMessage);
	let selectedFile = $state('');
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
				on:click={async () => {
					await onAction(message);
					message = defaultMessage;
					open = false;
				}}
				disabled={(!action && repoStatus.changes.length === 0) || message.length === 0}
				class="w-48"
			>
				{action ?? $t('deploy.commit')}
			</Button>
		</div>
	</div>
</Modal>
