<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, AccordionItem, Accordion } from 'flowbite-svelte';
	import type { PageData } from './$types';
	import { invalidate } from '$app/navigation';
	import DeployActions from '$lib/components/DeployActions.svelte';
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
			<Button color="alternative" on:click={() => revertLastCommit(historyList[0].SHA1)}>
				{$t('history.revert-commit', {
					values: { commit: historyList[0].SHA1, message: historyList[0].message }
				})}
			</Button>
			<DeployActions />
		</div>
	{/if}
	<ul class="list-disc ml-4">
		{#each historyList as history, index}
			<li class="mb-2 text-gray-600">
				<span class="text-gray-600">{history.message}</span>
				<span class="text-gray-400"> by {history.author}</span>
				<span class="text-gray-400"> on {history.date}</span>
				<span class="text-gray-400"> with hash {history.SHA1}</span>
			</li>
			<Accordion flush class="mr-4 mb-8">
				<AccordionItem tag="span" paddingFlush="py-2">
					<span slot="header">{$t('history.open-diff')}</span>
					{#each history.state_diff as line}
						<pre class={`text-sm ${lineColor(line)}`}>{line}</pre>
					{/each}
				</AccordionItem>
			</Accordion>
		{/each}
	</ul>
{/await}
