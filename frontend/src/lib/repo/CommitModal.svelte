<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Input, Modal } from 'flowbite-svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import { type FileChange, type RepoStatus } from '$lib/repo/repo';
	import FileIcon from 'lucide-svelte/icons/file';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';

	export let repoStatus: RepoStatus;

	let message = '';
	let selectedFile = '';

	$: selectedChange = repoStatus.changes.find((change) => change.path === selectedFile);
	$: stateJson = repoStatus.changes.find((change) => change.path === 'state.json');
	$: internalChanges = repoStatus.changes.filter((change) => change.path !== 'state.json');

	let fileClass =
		'flex items-center gap-1 text-base text-start text-gray-800 dark:text-gray-100 ' +
		'hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer p-1 px-2 rounded break-all ' +
		'whitespace-nowrap overflow-hidden text-ellipsis';
	let overflowClass = 'overflow-hidden text-ellipsis ';

	export let open = false;
</script>

<Modal
	bind:open
	title={$t('deploy.commit')}
	size="xl"
	outsideclose
	on:open={() => {
		if (stateJson) selectedFile = stateJson.path;
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
			<SplitPane type="horizontal" leftPaneClass="pr-1" min="15%" max="60%" pos="20%">
				<div class="flex flex-col" slot="a">
					{#if stateJson}
						<button
							class={fileClass +
								(selectedFile === stateJson.path ? ' bg-gray-100 dark:bg-gray-600' : '')}
							on:click={() => (selectedFile = stateJson.path)}
						>
							<FileIcon size="18" class="flex-shrink-0" />
							{stateJson.path}
						</button>
					{/if}
					<div class="flex text-base text-gray-800 dark:text-gray-100 p-1 mt-4 mb-1">
						{#if internalChanges.length === 0}
							{$t('history.no-internal-file-changes')}
						{:else}
							{$t('history.internal-file-changes', { values: { count: internalChanges.length } })}
						{/if}
					</div>
					{#each internalChanges as change}
						<button
							class={fileClass +
								(selectedFile === change.path ? ' bg-gray-100 dark:bg-gray-600' : '')}
							on:click={() => (selectedFile = change.path)}
							title={change.path}
						>
							<FileIcon size="18" class="flex-shrink-0" />
							<span>{change.file.split('.').slice(-2).join('.')}</span>
							<span class={overflowClass + 'text-gray-400 dark:text-gray-500'}>{change.dir}</span>
						</button>
					{/each}
				</div>
				<div slot="b">
					<div class="h-[calc(100vh-300px)] overflow-y-auto">
						{#if selectedChange}
							<MonospaceText code={selectedChange.diff} />
						{/if}
					</div>
				</div>
			</SplitPane>
		</div>
	</div>
</Modal>
