<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import { type FileChange, type RepoStatus } from '$lib/repo/repo';

	export let repoStatus: RepoStatus;

	let message = '';
	let selectedFile: FileChange | null = null;

	$: stateJson = repoStatus.changes.find((change) => change.file === 'state.json');

	let fileClass =
		'text-base text-start text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer p-1 rounded break-all';

	export let open = false;
</script>

<Modal
	bind:open
	title={$t('deploy.commit')}
	size="xl"
	outsideclose
	on:open={() => {
		if (stateJson) selectedFile = stateJson;
	}}
>
	<div>
		<div>
			<p class="text-base text-gray-900 dark:text-white mb-1">{$t('deploy.summary')}</p>
			<div class="flex flex-row gap-2">
				<Input type="text" bind:value={message} placeholder={$t('deploy.summary')} />
				<Button>{$t('deploy.commit')}</Button>
			</div>
		</div>
		<div class="flex gap-2 mt-4">
			<div class="w-64 flex-shrink-0 flex flex-col">
				{#if stateJson}
					<button
						class={fileClass + (selectedFile === stateJson ? ' bg-gray-100 dark:bg-gray-600' : '')}
						on:click={() => (selectedFile = stateJson)}
					>
						{stateJson.file}
					</button>
				{/if}
				<div class="flex text-base text-gray-900 dark:text-white p-1 mt-4 mb-1">
					{#if repoStatus.changes.length === 0}
						{$t('history.no-internal-file-changes')}
					{:else}
						{$t('history.internal-file-changes')}
					{/if}
				</div>
				{#each repoStatus.changes as change}
					{#if change.file !== 'state.json'}
						<button
							class={fileClass + (selectedFile === change ? ' bg-gray-100 dark:bg-gray-600' : '')}
							on:click={() => (selectedFile = change)}
						>
							{change.file}
						</button>
					{/if}
				{/each}
			</div>
			<div class="flex-grow h-[calc(100vh-300px)] overflow-y-auto">
				{#if selectedFile}
					<MonospaceText code={selectedFile.diff} />
				{/if}
			</div>
		</div>
	</div>
</Modal>
