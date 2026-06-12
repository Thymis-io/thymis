<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import { getDeviceType, getDeviceTypesMap } from '$lib/config/configUtils';
	import MonitorCheck from 'lucide-svelte/icons/monitor-check';
	import MonitorX from 'lucide-svelte/icons/monitor-x';
	import Server from 'lucide-svelte/icons/server';
	import Layers from 'lucide-svelte/icons/layers';
	import Tag from 'lucide-svelte/icons/tag';
	import OverviewConfigCard, { type ConfigCard } from '$lib/components/OverviewConfigCard.svelte';
	import FleetHealthChart from '$lib/components/FleetHealthChart.svelte';
	import FleetConnectivityChart from '$lib/components/FleetConnectivityChart.svelte';
	import OverviewInventory from '$lib/components/OverviewInventory.svelte';
	import OverviewTopDevices from '$lib/components/OverviewTopDevices.svelte';
	import { isOnline, isActive } from '$lib/deploymentInfo';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let deviceTypesMap = $derived(getDeviceTypesMap(data.availableModules));

	// Normalise to 7-char short hash so comparisons work regardless of
	// whether the API returns a full SHA1 or an already-shortened hash.
	let shortHeadCommit = $derived(data.headCommit?.slice(0, 7) ?? null);

	let configCards: ConfigCard[] = $derived.by(() => {
		return data.globalState.configs.map((cfg) => {
			const allInstances = data.deploymentInfos
				.filter((di) => di.deployed_config_id === cfg.identifier)
				.map((di) => {
					const shortCommit = di.deployed_config_commit?.slice(0, 7) ?? null;
					return {
						id: di.id,
						online: isOnline(di.last_seen),
						active: isActive(di.last_seen),
						lastSeen: di.last_seen,
						shortCommit,
						isCurrentCommit: !!shortCommit && shortCommit === shortHeadCommit
					};
				});

			const activeInstances = allInstances.filter((i) => i.active || i.online);

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

	// ── Summary stats ─────────────────────────────────────────────────────
	let onlineConfigsCount = $derived(configCards.filter((c) => c.onlineCount > 0).length);
	let totalConfigsCount = $derived(data.globalState.configs.length);
	let onlineInstancesCount = $derived(data.connectedDeploymentInfos.length);
	let tagsCount = $derived(data.globalState.tags.length);
	let activeInstancesTotal = $derived(
		configCards.reduce((sum, c) => sum + c.activeInstances.length, 0)
	);
	let offlineInstancesCount = $derived(Math.max(0, activeInstancesTotal - onlineInstancesCount));

	// ── Shared time-window control (fleet health + connectivity) ──────────
	type TimeWindow = '1h' | '24h' | '7d';
	let timewindow = $derived(data.timewindow as TimeWindow);

	const hoursMap: Record<TimeWindow, number> = { '1h': 1, '24h': 24, '7d': 7 * 24 };
	const granularityMap: Record<TimeWindow, '1min' | '15min' | '1h'> = {
		'1h': '1min',
		'24h': '15min',
		'7d': '1h'
	};

	function setTimeWindow(w: TimeWindow) {
		const sp = new URLSearchParams(page.url.search);
		sp.set('timewindow', w);
		sp.set('hours', hoursMap[w].toString());
		sp.set('granularity', granularityMap[w]);
		goto(`?${sp.toString()}`, { replaceState: true, invalidateAll: true });
	}

	let latestFleet = $derived(
		data.fleetMetrics.length ? data.fleetMetrics[data.fleetMetrics.length - 1] : null
	);
</script>

<PageHead title={$t('nav.overview')} subtitle={$t('overview.subtitle')} />

<!-- ── Row 1: stat cards ──────────────────────────────────────────────── -->
<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4 mb-4">
	<div class="ds-stat">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot online"></span>{$t('overview.stat.connected-devices')}
				</div>
				<div class="ds-stat-value">{onlineInstancesCount}</div>
			</div>
			<div class="ds-icon-tile online"><MonitorCheck class="h-[18px] w-[18px]" /></div>
		</div>
	</div>

	<div class="ds-stat">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot offline"></span>{$t('overview.offline')}
				</div>
				<div class="ds-stat-value">{offlineInstancesCount}</div>
			</div>
			<div class="ds-icon-tile offline"><MonitorX class="h-[18px] w-[18px]" /></div>
		</div>
	</div>

	<div class="ds-stat">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label">
					<span class="ds-stat-dot info"></span>{$t('overview.stat.configs-online')}
				</div>
				<div class="ds-stat-value">
					{onlineConfigsCount}<span class="ds-stat-sub">/{totalConfigsCount}</span>
				</div>
			</div>
			<div class="ds-icon-tile info"><Layers class="h-[18px] w-[18px]" /></div>
		</div>
	</div>

	<div class="ds-stat">
		<div class="flex items-start justify-between gap-3">
			<div>
				<div class="ds-stat-label"><span class="ds-stat-dot"></span>{$t('overview.stat.tags')}</div>
				<div class="ds-stat-value">{tagsCount}</div>
			</div>
			<div class="ds-icon-tile warning"><Tag class="h-[18px] w-[18px]" /></div>
		</div>
	</div>
</div>

<!-- ── Row 2: fleet average resource chips ────────────────────────────── -->
{#if latestFleet}
	<div class="mb-4 grid grid-cols-3 gap-4">
		<div class="ds-stat">
			<div class="ds-stat-label">{$t('overview.fleet.avg-cpu')}</div>
			<div class="ds-stat-value">{latestFleet.cpu_avg.toFixed(0)}%</div>
		</div>
		<div class="ds-stat">
			<div class="ds-stat-label">{$t('overview.fleet.avg-ram')}</div>
			<div class="ds-stat-value">{latestFleet.ram_avg.toFixed(0)}%</div>
		</div>
		<div class="ds-stat">
			<div class="ds-stat-label">{$t('overview.fleet.avg-disk')}</div>
			<div class="ds-stat-value">{latestFleet.disk_avg.toFixed(0)}%</div>
		</div>
	</div>
{/if}

<!-- ── Row 3: fleet health (full width) with shared time-window switch ── -->
<div class="ds-card mb-4 flex flex-col">
	<div class="ds-card-head flex items-center justify-between">
		<h3 class="ds-card-title">{$t('overview.chart.fleet-health')}</h3>
		<div class="flex gap-1">
			{#each ['1h', '24h', '7d'] as const as w}
				<button
					class="ds-btn ds-btn-sm {timewindow === w ? 'ds-btn-primary' : ''}"
					onclick={() => setTimeWindow(w)}
				>
					{w}
				</button>
			{/each}
		</div>
	</div>
	<div class="ds-card-pad">
		<FleetHealthChart metrics={data.fleetMetrics} {timewindow} />
	</div>
</div>

<!-- ── Row 4: connectivity + inventory/compliance ─────────────────────── -->
<div class="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.chart.connectivity')}</h3>
		</div>
		<div class="ds-card-pad">
			<FleetConnectivityChart points={data.connectivity} {timewindow} />
		</div>
	</div>

	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.chart.update-compliance')}</h3>
		</div>
		<OverviewInventory
			deploymentInfos={data.deploymentInfos}
			headCommit={data.headCommit}
			globalState={data.globalState}
			availableModules={data.availableModules}
		/>
	</div>
</div>

<!-- ── Row 5: top resource usage ──────────────────────────────────────── -->
<div class="ds-card mb-4 flex flex-col">
	<div class="ds-card-head">
		<h3 class="ds-card-title">{$t('overview.chart.top-load')}</h3>
	</div>
	<OverviewTopDevices devices={data.topDevices} />
</div>

<!-- ── Row 3: configurations ──────────────────────────────────────────── -->
<div class="mb-3 flex items-baseline gap-2">
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
				<OverviewConfigCard
					{config}
					globalState={data.globalState}
					deploymentInfos={data.deploymentInfos}
				/>
			</div>
		{/each}
	</div>
{/if}
