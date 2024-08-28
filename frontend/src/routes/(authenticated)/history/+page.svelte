<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, AccordionItem, Accordion, Tooltip, P } from 'flowbite-svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import Undo from 'lucide-svelte/icons/undo-2';
	export let data: PageData;

	const revertLastCommit = async (commitSHA: string) => {
		await fetch(`/api/history/revert-commit?commit_sha=${commitSHA}`, { method: 'POST' });
		await invalidate((url) => url.pathname === '/api/history' || url.pathname === '/api/state');
	};

	const lineColor = (line: string) => {
		if (line.startsWith('+')) {
			return 'text-green-400';
		} else if (line.startsWith('-')) {
			return 'text-red-400';
		} else if (line.startsWith('@@')) {
			return 'text-cyan-400';
		}
		return 'text-gray-200';
	};
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">History</h1>
</div>
{#await data.history}
	<p>Loading...</p>
{:then historyList}
	{#if historyList.length > 0}
		<div class="flex justify-between mb-4">
			<DeployActions />
		</div>
	{/if}
	<ul class="list-disc ml-4">
		{#each historyList as history, index}
			<li class="mb-2 text-gray-600">
				<div class="flex justify-between">
					<div>
						<span class="text-gray-600">{history.message}</span>
						<br />
						<span class="text-gray-400"> by {history.author}</span>
						<span class="text-gray-400"> on {history.date}</span>
						<span class="text-gray-400"> with hash {history.SHA1}</span>
					</div>
					<div class="shrink">
						<Button
							class="p-2 mr-2 w-full flex justify-center gap-2 rounded"
							color="alternative"
							on:click={() => revertLastCommit(history.SHA1)}
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
