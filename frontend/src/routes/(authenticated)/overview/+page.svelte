<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import PieChart from '$lib/components/PieChart.svelte';
	import type { PieSlice } from '$lib/components/PieChart.svelte';
	import { getDeviceType, getDeviceTypesMap } from '$lib/config/configUtils';
	import MonitorCheck from 'lucide-svelte/icons/monitor-check';
	import MonitorX from 'lucide-svelte/icons/monitor-x';
	import Server from 'lucide-svelte/icons/server';
	import Layers from 'lucide-svelte/icons/layers';
	import Tag from 'lucide-svelte/icons/tag';
	import OverviewConfigCard, { type ConfigCard } from '$lib/components/OverviewConfigCard.svelte';
	import { isOnline, isActive } from '$lib/deploymentInfo';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const HEAD_COLOR = '#10b981'; // emerald-500
	const SLICE_COLORS = [
		'#3b82f6', // blue-500
		'#f59e0b', // amber-500
		'#ef4444', // red-500
		'#8b5cf6', // violet-500
		'#ec4899', // pink-500
		'#14b8a6', // teal-500
		'#f97316', // orange-500
		'#6366f1', // indigo-500
		'#84cc16' // lime-500
	];

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

	// ── Pie 1: deployed commit — active instances only, HEAD highlighted ──
	let commitSlices: PieSlice[] = $derived.by(() => {
		const counts = new Map<string, number>();
		for (const card of configCards) {
			for (const inst of card.activeInstances) {
				const commit = inst.shortCommit ?? $t('overview.no-commit');
				counts.set(commit, (counts.get(commit) ?? 0) + 1);
			}
		}
		const entries = Array.from(counts.entries()).sort((a, b) => {
			if (a[0] === shortHeadCommit) return -1;
			if (b[0] === shortHeadCommit) return 1;
			return b[1] - a[1];
		});
		let colorIndex = 0;
		return entries.map(([label, value]) => {
			const isHead = label === shortHeadCommit;
			const color = isHead ? HEAD_COLOR : SLICE_COLORS[colorIndex++ % SLICE_COLORS.length];
			return { label, value, color, isHead };
		});
	});

	// ── Pie 2: online vs offline — only among active instances ───────────
	let onlineStatusSlices: PieSlice[] = $derived.by(() => {
		const activeTotal = configCards.reduce((sum, c) => sum + c.activeInstances.length, 0);
		const offline = activeTotal - onlineInstancesCount;
		const slices: PieSlice[] = [];
		if (onlineInstancesCount > 0)
			slices.push({ label: $t('overview.online'), value: onlineInstancesCount, color: '#10b981' });
		if (offline > 0)
			slices.push({ label: $t('overview.offline'), value: offline, color: '#6b7280' });
		return slices;
	});
</script>

<PageHead
	title={$t('nav.overview')}
	subtitle={$t('overview.subtitle')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

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

<!-- ── Row 2: charts ──────────────────────────────────────────────────── -->
<div class="grid grid-cols-1 gap-4 md:grid-cols-2 mb-4">
	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.chart.deployed-commits')}</h3>
		</div>
		<div class="ds-card-pad flex flex-1 items-center justify-center">
			<PieChart slices={commitSlices} size={180} />
		</div>
	</div>

	<div class="ds-card flex flex-col">
		<div class="ds-card-head">
			<h3 class="ds-card-title">{$t('overview.chart.online-status')}</h3>
		</div>
		<div class="ds-card-pad flex flex-1 items-center justify-center">
			<PieChart slices={onlineStatusSlices} size={180} />
		</div>
	</div>
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
