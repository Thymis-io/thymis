<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import Server from 'lucide-svelte/icons/server';
	import OverviewConfigCard, { type ConfigCard } from '$lib/components/OverviewConfigCard.svelte';
	import OverviewKpiCards from '$lib/components/OverviewKpiCards.svelte';
	import FleetConnectivityChart from '$lib/components/FleetConnectivityChart.svelte';
	import OverviewAvailabilityHeatmap from '$lib/components/OverviewAvailabilityHeatmap.svelte';
	import OverviewAlerts from '$lib/components/OverviewAlerts.svelte';
	import OverviewVersions from '$lib/components/OverviewVersions.svelte';
	import OverviewDeviceTypes from '$lib/components/OverviewDeviceTypes.svelte';
	import OverviewTopDevices from '$lib/components/OverviewTopDevices.svelte';
	import TimeRangeSelector from '$lib/components/TimeRangeSelector.svelte';
	import { getDeviceType, getDeviceTypesMap } from '$lib/config/configUtils';
	import { isOnline } from '$lib/deploymentInfo';
	import type { TimeRange } from '$lib/fleet';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deviceTypesMap = $derived(getDeviceTypesMap(data.availableModules));
	let shortHeadCommit = $derived(data.headCommit?.slice(0, 7) ?? null);

	let configCards: ConfigCard[] = $derived.by(() => {
		return data.globalState.configs.map((cfg) => {
			const activeInstances = data.globalState.deploymentInfos
				.filter((di) => di.deployed_config_id === cfg.identifier)
				.filter((di) => !di.archived)
				.map((di) => {
					const shortCommit = di.deployed_config_commit?.slice(0, 7) ?? null;
					return {
						id: di.id,
						online: isOnline(di.last_seen),
						lastSeen: di.last_seen,
						shortCommit,
						isCurrentCommit: !!shortCommit && shortCommit === shortHeadCommit
					};
				});
			const rawType = getDeviceType(cfg);
			const deviceTypeLabel = rawType
				? rawType in deviceTypesMap
					? deviceTypesMap[rawType]
					: rawType
				: $t('overview.unknown-device-type');
			const onlineCount = activeInstances.filter((i) => i.online).length;
			return {
				identifier: cfg.identifier,
				displayName: cfg.displayName,
				deviceTypeLabel,
				activeInstances,
				onlineCount
			};
		});
	});

	// KPIs
	let onlineInstancesCount = $derived(data.connectedDeploymentInfos.length);
	let activeInstancesTotal = $derived(
		configCards.reduce((sum, c) => sum + c.activeInstances.length, 0)
	);
	let offlineInstancesCount = $derived(Math.max(0, activeInstancesTotal - onlineInstancesCount));
	let onlineConfigsCount = $derived(configCards.filter((c) => c.onlineCount > 0).length);
	let totalConfigsCount = $derived(data.globalState.configs.length);

	let behindCount = $derived.by(() => {
		const active = data.globalState.deploymentInfos.filter((di) => !di.archived);
		return active.filter(
			(di) => (di.deployed_config_commit?.slice(0, 7) ?? null) !== shortHeadCommit
		).length;
	});

	// Time range
	let range = $derived(data.range as TimeRange);

	function setRange(r: TimeRange) {
		const sp = new URLSearchParams(page.url.search);
		sp.set('range', r);
		sp.delete('hours');
		goto(`?${sp.toString()}`, { replaceState: true, invalidateAll: true });
	}
	function setCustom(hours: number) {
		const sp = new URLSearchParams(page.url.search);
		sp.delete('range');
		sp.set('hours', Math.round(hours).toString());
		goto(`?${sp.toString()}`, { replaceState: true, invalidateAll: true });
	}

	let connTimewindow = $derived(range === '24h' ? '24h' : '7d') as '1h' | '24h' | '7d';
</script>

<PageHead title={$t('nav.overview')} subtitle={$t('overview.subtitle')} />

<!-- Row 1: KPI cards -->
<div class="mb-4">
	<OverviewKpiCards
		onlineCount={onlineInstancesCount}
		offlineCount={offlineInstancesCount}
		{onlineConfigsCount}
		{totalConfigsCount}
		{behindCount}
	/>
</div>

<!-- Row 2: connectivity over time with range selector -->
<div class="ds-card mb-4 flex flex-col">
	<div class="ds-card-head flex items-center justify-between">
		<h3 class="ds-card-title">{$t('overview.chart.connectivity')}</h3>
		<TimeRangeSelector value={range} onSelect={setRange} />
	</div>
	<div class="ds-card-pad">
		<FleetConnectivityChart points={data.connectivity} timewindow={connTimewindow} />
	</div>
</div>

<!-- Row 3: availability heatmap + alerts -->
<div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.availability.title')}</h3>
		</div>
		<OverviewAvailabilityHeatmap globalState={data.globalState} availability={data.availability} />
	</div>
	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.alerts.title')}</h3>
		</div>
		<OverviewAlerts alerts={data.alerts} />
	</div>
</div>

<!-- Row 4: software versions + device types -->
<div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
	<div id="software-versions" class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.versions.title')}</h3>
		</div>
		<OverviewVersions globalState={data.globalState} headCommit={data.headCommit} />
	</div>
	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.device-types.title')}</h3>
		</div>
		<OverviewDeviceTypes globalState={data.globalState} availableModules={data.availableModules} />
	</div>
</div>

<!-- Row 5: top resource usage -->
<div class="ds-card mb-4 flex flex-col">
	<div class="ds-card-head">
		<h3 class="ds-card-title">{$t('overview.chart.top-load')}</h3>
	</div>
	<OverviewTopDevices globalState={data.globalState} devices={data.topDevices} />
</div>

<!-- Row 6: configurations -->
<div id="configurations" class="mb-3 flex items-baseline gap-2">
	<h2 class="ds-card-title" style="font-size: 15px">{$t('overview.section-configurations')}</h2>
	<span class="ds-card-sub">{totalConfigsCount}</span>
</div>

{#if configCards.length === 0}
	<div class="ds-card ds-card-pad py-10 text-center">
		<Server class="mx-auto mb-3 h-10 w-10" style="color: var(--ds-text-mute)" />
		<p class="text-sm" style="color: var(--ds-text-dim)">{$t('overview.no-configs')}</p>
	</div>
{:else}
	<div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
		{#each configCards as config (config.identifier)}
			<div class="ds-card flex flex-col overflow-hidden">
				<OverviewConfigCard {config} globalState={data.globalState} />
			</div>
		{/each}
	</div>
{/if}
