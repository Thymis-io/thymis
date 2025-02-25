<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import { type FileChange, type RepoStatus } from '$lib/repo/repo';
	import FileIcon from 'lucide-svelte/icons/file';

	export let repoStatus: RepoStatus;

	let message = '';
	let selectedFile = '';

	$: selectedChange = repoStatus.changes.find((change) => change.file === selectedFile);
	$: stateJson = repoStatus.changes.find((change) => change.file === 'state.json');
	$: internalChanges = repoStatus.changes.filter((change) => change.file !== 'state.json');

	let fileClass =
		'flex items-center gap-2 text-base text-start text-gray-900 dark:text-white ' +
		'hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer p-1 px-2 rounded break-all';

	export let open = false;
</script>

<Modal
	bind:open
	title={$t('deploy.commit')}
	size="xl"
	outsideclose
	on:open={() => {
		if (stateJson) selectedFile = stateJson.file;
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
						class={fileClass +
							(selectedFile === stateJson.file ? ' bg-gray-100 dark:bg-gray-600' : '')}
						on:click={() => (selectedFile = stateJson.file)}
					>
						<FileIcon size="18" class="flex-shrink-0" />
						{stateJson.file}
					</button>
				{/if}
				<div class="flex text-base text-gray-900 dark:text-white p-1 mt-4 mb-1">
					{#if internalChanges.length === 0}
						{$t('history.no-internal-file-changes')}
					{:else}
						{$t('history.internal-file-changes', { values: { count: internalChanges.length } })}
					{/if}
				</div>
				{#each internalChanges as change}
					<button
						class={fileClass +
							(selectedFile === change.file ? ' bg-gray-100 dark:bg-gray-600' : '')}
						on:click={() => (selectedFile = change.file)}
					>
						<FileIcon size="18" class="flex-shrink-0" />
						{change.file}
					</button>
				{/each}
			</div>
			<div class="flex-grow h-[calc(100vh-300px)] overflow-y-auto">
				{#if selectedChange}
					<MonospaceText code={selectedChange.diff} />
				{/if}
			</div>
		</div>
	</div>
</Modal>
