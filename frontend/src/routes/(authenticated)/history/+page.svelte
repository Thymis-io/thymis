<script lang="ts">
	import { t } from 'svelte-i18n';
	import { AccordionItem, Accordion, Tooltip, P } from 'flowbite-svelte';
	import type { PageData } from './$types';
	import RollbackModal from './RollbackModal.svelte';
	import type { Commit } from '$lib/history';
	import PageHead from '$lib/components/PageHead.svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import { diff } from 'svelte-highlight/languages';

	export let data: PageData;

	let revertCommit: Commit | undefined;

	const fetchDiff = async (refA: string, refB: string) => {
		const res = await fetchWithNotify(`/api/history/diff?refA=${refA}&refB=${refB}`);
		return (await res.json()) as string[];
	};
</script>

<PageHead title={$t('nav.history')} />
<RollbackModal bind:commit={revertCommit} />
<ul class="list-disc ml-4">
	{#each data.history as history, index}
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
					<!-- <Button
							class="p-2 mr-2 w-full flex justify-center gap-2 rounded"
							color="alternative"
							on:click={() => (revertCommit = history)}
							disabled={index === 0}
						>
							<Undo />
							{$t('history.revert-commit-button')}
						</Button> -->
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
		<Accordion flush class="mr-4 mb-8">
			<AccordionItem tag="span" paddingFlush="py-2" transitionType="fly">
				<span slot="header">{$t('history.open-diff')}</span>
				{#await fetchDiff(index !== data.history.length - 1 ? `${history.SHA1}~1` : '', index !== 0 ? history.SHA1 : '') then diffCode}
					<MonospaceText language={diff} code={diffCode} />
				{/await}
			</AccordionItem>
		</Accordion>
	{/each}
</ul>
