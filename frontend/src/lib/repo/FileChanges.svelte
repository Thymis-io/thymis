<script lang="ts">
	import { t } from 'svelte-i18n';
	import SplitPane from '$lib/splitpane/SplitPane.svelte';
	import type { RepoStatus } from './repo';
	import FileIcon from 'lucide-svelte/icons/file';
	import MonospaceText from '$lib/components/MonospaceText.svelte';

	interface Props {
		selectedFile?: string;
		repoStatus: RepoStatus;
	}

	let { selectedFile = $bindable(''), repoStatus }: Props = $props();

	let selectedChange = $derived(repoStatus.changes.find((change) => change.path === selectedFile));
	let stateJson = $derived(repoStatus.changes.find((change) => change.path === 'state.json'));
	let internalChanges = $derived(
		repoStatus.changes.filter((change) => change.path !== 'state.json')
	);

	let textClass = 'text-base text-gray-800 dark:text-gray-100 ';
	let selectedClass = 'bg-gray-100 dark:bg-gray-600 ';
	let fileClass =
		textClass +
		'flex items-center gap-1 p-1 px-2 text-start ' +
		'hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer rounded break-all ' +
		'whitespace-nowrap overflow-hidden text-ellipsis ';
	let overflowClass = 'overflow-hidden text-ellipsis ';
</script>

<div class="h-full overflow-hidden">
	<SplitPane type="horizontal" leftPaneClass="pr-2" min="15%" max="60%" pos="20%">
		{#snippet a()}
			<div class="flex flex-col">
				{#if stateJson}
					<button
						class={fileClass + (selectedFile === stateJson.path ? selectedClass : '')}
						onclick={() => (selectedFile = stateJson.path)}
					>
						<FileIcon size="18" class="flex-shrink-0" />
						{stateJson.path}
					</button>
				{/if}
				<div class={textClass + 'flex p-1 mt-4 mb-1'}>
					{#if internalChanges.length === 0}
						{$t('history.no-internal-file-changes')}
					{:else}
						{$t('history.internal-file-changes', { values: { count: internalChanges.length } })}
					{/if}
				</div>
				{#each internalChanges as change}
					<button
						class={fileClass + (selectedFile === change.path ? selectedClass : '')}
						onclick={() => (selectedFile = change.path)}
						title={change.path}
					>
						<FileIcon size="18" class="flex-shrink-0" />
						<span>{change.file.split('.').slice(-2).join('.')}</span>
						<span class={overflowClass + 'text-gray-400 dark:text-gray-500'}>{change.dir}</span>
					</button>
				{/each}
			</div>
		{/snippet}
		{#snippet b()}
			<div>
				<div class="h-full overflow-y-auto">
					{#if selectedChange}
						<MonospaceText code={selectedChange.diff} />
					{/if}
				</div>
			</div>
		{/snippet}
	</SplitPane>
</div>
