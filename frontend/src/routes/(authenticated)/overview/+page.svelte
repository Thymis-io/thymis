<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Card } from 'flowbite-svelte';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import PieChart from '$lib/components/PieChart.svelte';
	import type { PieSlice } from '$lib/components/PieChart.svelte';
	import { getDeviceType, getDeviceTypesMap } from '$lib/config/configUtils';
	import MonitorCheck from 'lucide-svelte/icons/monitor-check';
	import Server from 'lucide-svelte/icons/server';
	import Layers from 'lucide-svelte/icons/layers';
	import Tag from 'lucide-svelte/icons/tag';
	import OverviewConfigCard from '$lib/components/OverviewConfigCard.svelte';

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

	const ONLINE_THRESHOLD_MS = 30_000;
	// DeploymentInfos older than this are stale ghosts (e.g. SD card reflashed)
	// and should not inflate the "N/M online" count.
	const STALE_THRESHOLD_MS = 7 * 24 * 60 * 60 * 1000;

	// ── Helpers ──────────────────────────────────────────────────────────
	function isOnline(lastSeen: string | null): boolean {
		return !!lastSeen && Date.now() - new Date(lastSeen).getTime() < ONLINE_THRESHOLD_MS;
	}
	function isActive(lastSeen: string | null): boolean {
		return !!lastSeen && Date.now() - new Date(lastSeen).getTime() < STALE_THRESHOLD_MS;
	}

	// ── Device type map ───────────────────────────────────────────────────
	let deviceTypesMap = $derived(getDeviceTypesMap(data.availableModules));

	// ── Per-config enriched data ──────────────────────────────────────────
	// The right mental model: a Config IS the "device" the user thinks about.
	// DeploymentInfos are the physical hardware instances running that config.
	// "Active" = seen within 7 days. Older records are stale ghosts from
	// previous SD card flashes and must not inflate the online/offline count.
	type ConfigInstance = {
		id: string;
		online: boolean;
		active: boolean;
		lastSeen: string | null;
		shortCommit: string | null;
		isCurrentCommit: boolean;
	};

	type ConfigCard = {
		identifier: string;
		displayName: string;
		deviceTypeLabel: string;
		activeInstances: ConfigInstance[];
		onlineCount: number;
	};

	// Normalise to 7-char short hash so comparisons work regardless of
	// whether the API returns a full SHA1 or an already-shortened hash.
	let shortHeadCommit = $derived(data.headCommit?.slice(0, 7) ?? null);

	let configCards = $derived((): ConfigCard[] => {
		return data.globalState.configs.map((cfg) => {
			const allInstances: ConfigInstance[] = data.deploymentInfos
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

			// Only count instances seen within 7 days — stale ghosts are invisible
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
	let onlineConfigsCount = $derived(configCards().filter((c) => c.onlineCount > 0).length);
	let totalConfigsCount = $derived(data.globalState.configs.length);
	let onlineInstancesCount = $derived(data.connectedDeploymentInfos.length);
	let tagsCount = $derived(data.globalState.tags.length);

	// ── Pie 1: deployed commit — active instances only, HEAD highlighted ──
	let commitSlices = $derived((): PieSlice[] => {
		const counts = new Map<string, number>();
		for (const card of configCards()) {
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
	let onlineStatusSlices = $derived((): PieSlice[] => {
		const activeTotal = configCards().reduce((sum, c) => sum + c.activeInstances.length, 0);
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
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

<!-- ── Row 1: stat cards ──────────────────────────────────────────────── -->
<div class="mb-4 flex flex-wrap items-start gap-4">
	<Card padding="none" class="p-4">
		<div class="flex items-center gap-3">
			<div
				class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-900"
			>
				<MonitorCheck class="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
			</div>
			<div>
				<p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
					{onlineInstancesCount}
				</p>
				<p class="text-xs text-gray-500 dark:text-gray-400">
					{$t('overview.stat.connected-devices')}
				</p>
			</div>
		</div>
	</Card>
	<Card padding="none" class="p-4">
		<div class="flex items-center gap-3">
			<div
				class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-primary-100 dark:bg-primary-900"
			>
				<Layers class="h-5 w-5 text-primary-600 dark:text-primary-400" />
			</div>
			<div>
				<p class="text-2xl font-bold text-primary-600 dark:text-primary-400">
					{onlineConfigsCount}<span class="text-base font-normal text-gray-400 dark:text-gray-500"
						>/{totalConfigsCount}</span
					>
				</p>
				<p class="text-xs text-gray-500 dark:text-gray-400">{$t('overview.stat.configs-online')}</p>
			</div>
		</div>
	</Card>
	<Card padding="none" class="p-4">
		<div class="flex items-center gap-3">
			<div
				class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900"
			>
				<Tag class="h-5 w-5 text-amber-600 dark:text-amber-400" />
			</div>
			<div>
				<p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{tagsCount}</p>
				<p class="text-xs text-gray-500 dark:text-gray-400">{$t('overview.stat.tags')}</p>
			</div>
		</div>
	</Card>
</div>

<!-- ── Row 2: charts + device grid side by side ───────────────────────── -->
<div class="flex flex-wrap items-start gap-4">
	<!-- Deployed commits chart -->
	<Card padding="none" class="flex flex-col items-center gap-2 p-4">
		<span class="text-xs font-semibold text-gray-600 dark:text-gray-300"
			>{$t('overview.chart.deployed-commits')}</span
		>
		<PieChart slices={commitSlices()} size={180} />
	</Card>

	<!-- Online / offline chart -->
	<Card padding="none" class="flex flex-col items-center gap-2 p-4">
		<span class="text-xs font-semibold text-gray-600 dark:text-gray-300"
			>{$t('overview.chart.online-status')}</span
		>
		<PieChart slices={onlineStatusSlices()} size={180} />
	</Card>

	<!-- Device grid -->
	{#if configCards().length === 0}
		<Card padding="none" class="p-8 text-center">
			<Server class="mx-auto mb-3 h-10 w-10 text-gray-300 dark:text-gray-600" />
			<p class="text-sm text-gray-500 dark:text-gray-400">{$t('overview.no-configs')}</p>
		</Card>
	{:else}
		<div class="flex flex-row flex-wrap w-full gap-4">
			{#each configCards() as config (config.identifier)}
				<OverviewConfigCard {config} globalState={data.globalState} />
			{/each}
		</div>
	{/if}
</div>
