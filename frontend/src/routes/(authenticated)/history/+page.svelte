<script lang="ts">
	import { t } from 'svelte-i18n';
	import { AccordionItem, Accordion } from 'flowbite-svelte';
	import type { PageData } from './$types';
	import RollbackModal from './RollbackModal.svelte';
	import type { Commit } from '$lib/history';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import { diff } from 'svelte-highlight/languages';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let revertCommit: Commit | undefined = $state();

	const formatCommitDate = (raw: string) => {
		const date = new Date(raw);
		if (isNaN(date.getTime())) return raw;
		return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
	};

	const fetchDiff = async (refA: string, refB: string) => {
		const res = await fetchWithNotify(`/api/history/diff?refA=${refA}&refB=${refB}`);
		return (await res.json()) as string;
	};
</script>

<PageHead
	title={$t('nav.history')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>
<RollbackModal bind:commit={revertCommit} />
<div class="flex flex-col gap-3">
	{#each data.history as history, index}
		<div class="ds-card">
			<div class="ds-card-pad">
				<div class="flex items-start justify-between gap-4">
					<div class="min-w-0">
						<p class="text-sm font-semibold" style="color: var(--ds-text)">{history.message}</p>
						<p
							class="mt-1 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-xs"
							style="color: var(--ds-text-dim)"
						>
							<span>by {history.author}</span>
							<span aria-hidden="true">·</span>
							<span
								class="playwright-snapshot-unstable"
								title={new Date(history.date).toISOString()}
							>
								{formatCommitDate(history.date)}
							</span>
							<span aria-hidden="true">·</span>
							<span style="color: var(--ds-text-mute)">
								<RenderTimeAgo timestamp={history.date} class="playwright-snapshot-unstable" />
							</span>
							<span aria-hidden="true">·</span>
							<span class="playwright-snapshot-unstable ds-mono">{history.SHA1}</span>
						</p>
					</div>
				</div>
				<Accordion flush class="mt-2">
					<AccordionItem tag="span" paddingFlush="py-2" transitionType="fly">
						{#snippet header()}
							<span class="text-sm" style="color: var(--ds-accent-strong)"
								>{$t('history.open-diff')}</span
							>
						{/snippet}
						{#await fetchDiff(index !== data.history.length - 1 ? `${history.SHA1}~1` : '', index !== 0 ? history.SHA1 : '') then diffCode}
							<MonospaceText language={diff} code={diffCode} />
						{/await}
					</AccordionItem>
				</Accordion>
			</div>
		</div>
	{/each}
</div>
