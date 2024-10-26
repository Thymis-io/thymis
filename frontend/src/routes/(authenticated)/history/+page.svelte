<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, AccordionItem, Accordion, Tooltip, P, Spinner } from 'flowbite-svelte';
	import type { PageData } from './$types';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import Undo from 'lucide-svelte/icons/undo-2';
	import Settings from 'lucide-svelte/icons/settings';
	import RollbackModal from './RollbackModal.svelte';
	import type { Commit } from '$lib/history';

	export let data: PageData;

	let revertCommit: Commit | undefined;

	const lineColor = (line: string) => {
		if (line.startsWith('+')) {
			return 'text-green-500 fark:text-green-400';
		} else if (line.startsWith('-')) {
			return 'text-red-500 dark:text-red-400';
		} else if (line.startsWith('@@')) {
			return 'text-cyan-600 dark:text-cyan-400';
		}
		return 'text-gray-700 dark:text-gray-200';
	};
</script>

<RollbackModal bind:commit={revertCommit} />
<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">History</h1>
	<DeployActions />
</div>
{#await data.history_and_git_info}
	<p>Loading...</p>
{:then [historyList, gitInfo]}
	<div class="my-8 flex items-end">
		<a href="/git-config">
			<Button class="gap-2 whitespace-nowrap" color="alternative">
				<Settings size={20} />
				{$t('history.git-settings')}
			</Button>
		</a>
	</div>
	<ul class="list-disc ml-4">
		{#each historyList as history, index}
			<li class="mb-2 text-gray-600">
				<div class="flex justify-between">
					<div>
						<span class="text-gray-600 dark:text-gray-400">{history.message}</span>
						<br />
						<span class="text-gray-400 dark:text-gray-600"> by {history.author}</span>
						<span class="text-gray-400 dark:text-gray-600"> on {history.date}</span>
						<span class="text-gray-400 dark:text-gray-600"> with hash {history.SHA1}</span>
					</div>
					<div class="shrink">
						<Button
							class="p-2 mr-2 w-full flex justify-center gap-2 rounded"
							color="alternative"
							on:click={() => (revertCommit = history)}
							disabled={index === 0}
						>
							<Undo />
							{$t('history.revert-commit-button')}
						</Button>
						<Tooltip type="auto">
							<P size="sm">
								{#if index === 0}
									{$t('history.no-revert')}
								{:else}
									{$t('history.revert-commit')}
								{/if}
							</P>
						</Tooltip>
					</div>
				</div>
			</li>
			{#if history.state_diff.length > 0}
				<Accordion flush class="mr-4 mb-8">
					<AccordionItem tag="span" paddingFlush="py-2">
						<span slot="header">{$t('history.open-diff')}</span>
						{#each history.state_diff as line}
							<pre class={`text-sm ${lineColor(line)}`}>{line}</pre>
						{/each}
					</AccordionItem>
				</Accordion>
			{:else}
				<p class="mb-8 text-gray-600">No state changes</p>
			{/if}
		{/each}
	</ul>
{/await}
