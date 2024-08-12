<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button } from 'flowbite-svelte';
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
		} else if(line.startsWith('@@')) {
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
{:then history}
	{#if history.length > 0}
		<div class="flex justify-between mb-4">
			<Button color="alternative" on:click={() => revertLastCommit(history[0].SHA1)}>
				{$t('history.revert-commit', {
					values: { commit: history[0].SHA1, message: history[0].message }
				})}
			</Button>
			<DeployActions />
		</div>
	{/if}
	<ul class="list-disc ml-4">
		{#each history as h}
			<!-- simple left-bound list -->
			<li class="mb-2 text-gray-600">
				<!-- {h.message} by {h.author} on {h.date} with hash {h.hash} -->
				<span class="text-gray-600">{h.message}</span>
				<span class="text-gray-400"> by {h.author}</span>
				<span class="text-gray-400"> on {h.date}</span>
				<span class="text-gray-400"> with hash {h.SHA1}</span>
			</li>
			{#each h.state_diff as line}
				<pre class={lineColor(line)}>{line}</pre>
			{/each}
		{/each}
	</ul>
{/await}
