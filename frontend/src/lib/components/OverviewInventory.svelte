<script lang="ts">
	import { t } from 'svelte-i18n';
	import PieChart, { type PieSlice } from '$lib/components/PieChart.svelte';
	import { isActive, type DeploymentInfo } from '$lib/deploymentInfo';
	import { getDeviceType, getDeviceTypesMap } from '$lib/config/configUtils';
	import type { GlobalState } from '$lib/state.svelte';
	import type { Module } from '$lib/state';

	interface Props {
		deploymentInfos: DeploymentInfo[];
		headCommit: string | null;
		globalState: GlobalState;
		availableModules: Module[];
	}
	let { deploymentInfos, headCommit, globalState, availableModules }: Props = $props();

	const shortHead = $derived(headCommit?.slice(0, 7) ?? null);

	const active = $derived(deploymentInfos.filter((di) => isActive(di.last_seen)));

	const onHead = $derived(
		active.filter((di) => (di.deployed_config_commit?.slice(0, 7) ?? null) === shortHead).length
	);
	const behind = $derived(active.length - onHead);
	const compliancePct = $derived(active.length ? Math.round((onHead / active.length) * 100) : 0);

	const deviceTypesMap = $derived(getDeviceTypesMap(availableModules));
	const configByIdentifier = $derived(
		new Map(globalState.configs.map((cfg) => [cfg.identifier, cfg]))
	);

	const typeSlices: PieSlice[] = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const di of active) {
			const cfg = di.deployed_config_id ? configByIdentifier.get(di.deployed_config_id) : undefined;
			const rawType = cfg ? getDeviceType(cfg) : undefined;
			const label = rawType
				? (deviceTypesMap[rawType] ?? rawType)
				: $t('overview.unknown-device-type');
			counts.set(label, (counts.get(label) ?? 0) + 1);
		}
		const colors = ['#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];
		return Array.from(counts.entries()).map(([label, value], i) => ({
			label,
			value,
			color: colors[i % colors.length]
		}));
	});
</script>

<div class="ds-card-pad space-y-5">
	<!-- Compliance bar -->
	<div>
		<div class="mb-1 flex items-baseline justify-between text-sm">
			<span style="color: var(--ds-text)">{$t('overview.fleet.on-head')}</span>
			<span style="color: var(--ds-text-dim)">{onHead}/{active.length} · {compliancePct}%</span>
		</div>
		<div class="h-2.5 w-full overflow-hidden rounded-full" style="background: var(--ds-border)">
			<div class="h-full rounded-full bg-emerald-500" style="width: {compliancePct}%"></div>
		</div>
		{#if behind > 0}
			<p class="mt-1 text-xs" style="color: var(--ds-text-dim)">
				{behind}
				{$t('overview.fleet.behind')}
			</p>
		{/if}
	</div>

	<!-- Device type distribution -->
	{#if typeSlices.length}
		<div>
			<h4 class="mb-2 text-xs font-semibold" style="color: var(--ds-text-dim)">
				{$t('overview.fleet.device-types')}
			</h4>
			<div class="flex items-center justify-center">
				<PieChart slices={typeSlices} size={150} />
			</div>
		</div>
	{/if}
</div>
