<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		headCommit: string | null;
	}
	let { globalState, headCommit }: Props = $props();

	const shortHead = $derived(headCommit?.slice(0, 7) ?? null);
	const active = $derived(globalState.deploymentInfos.filter((di) => !di.archived));

	type VersionGroup = { commit: string; count: number; isHead: boolean; ids: string[] };

	const groups = $derived.by<VersionGroup[]>(() => {
		const map = new Map<string, VersionGroup>();
		for (const di of active) {
			const commit = di.deployed_config_commit?.slice(0, 7) ?? $t('overview.no-commit');
			const g = map.get(commit) ?? {
				commit,
				count: 0,
				isHead: commit === shortHead,
				ids: []
			};
			g.count += 1;
			g.ids.push(di.id);
			map.set(commit, g);
		}
		return Array.from(map.values()).sort((a, b) => b.count - a.count);
	});

	const onHead = $derived(groups.find((g) => g.isHead)?.count ?? 0);
	const behind = $derived(active.length - onHead);
	const total = $derived(active.length);

	function barColor(g: VersionGroup): string {
		return g.isHead ? '#10b981' : '#f59e0b';
	}
</script>

<div class="ds-card-pad space-y-3">
	<div class="flex items-baseline justify-between text-sm">
		<span style="color: var(--ds-text)">{$t('overview.versions.up-to-date')}</span>
		<span style="color: var(--ds-text-dim)">{onHead}/{total}</span>
	</div>

	{#if behind > 0}
		<p class="text-xs" style="color: #f59e0b">
			{behind}
			{$t('overview.versions.behind')}
		</p>
	{/if}

	<div class="space-y-2">
		{#each groups as g (g.commit)}
			<div>
				<div class="mb-1 flex items-baseline justify-between text-xs">
					<span class="font-mono" style="color: var(--ds-text)">
						{g.commit}{g.isHead ? ` · ${$t('overview.versions.latest')}` : ''}
					</span>
					<span style="color: var(--ds-text-dim)">{g.count}</span>
				</div>
				<div class="h-2 w-full overflow-hidden rounded-full" style="background: var(--ds-border)">
					<div
						class="h-full rounded-full"
						style="width: {total ? (g.count / total) * 100 : 0}%; background: {barColor(g)}"
					></div>
				</div>
			</div>
		{/each}
	</div>
</div>
