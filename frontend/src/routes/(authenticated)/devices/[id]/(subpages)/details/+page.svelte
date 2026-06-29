<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import SectionMetrics from '../../SectionMetrics.svelte';
	import SectionSwitchConfig from '../../SectionSwitchConfig.svelte';
	import SectionDeviceInfo from '../../SectionDeviceInfo.svelte';
	import SectionOnlineStatus from '../../SectionOnlineStatus.svelte';
	import SectionErrorLogs from '../../SectionErrorLogs.svelte';
	import Section from '$lib/components/layout/Section.svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { queryParameters } from 'sveltekit-search-params';

	const params = queryParameters();

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $derived(
		data.globalState.deploymentInfos.find((di) => di.id === data.deploymentInfoId)!
	);
	let config = $derived(
		data.globalState.configs.find((c) => c.identifier === deploymentInfo.deployed_config_id)
	);

	type TimeWindow = '1h' | '24h' | '7d';
	let metricsTimeWindow: TimeWindow = $derived.by(() => {
		const tw = params['timewindow'];
		if (tw === '1h' || tw === '24h' || tw === '7d') return tw;
		return '24h';
	});

	const hoursMap: Record<TimeWindow, number> = { '1h': 1, '24h': 24, '7d': 7 * 24 };
	const granularityMap: Record<TimeWindow, '1min' | '15min' | '1h'> = {
		'1h': '1min',
		'24h': '15min',
		'7d': '1h'
	};

	async function handleTimeWindowChange(window: TimeWindow) {
		const searchParams = new URLSearchParams(page.url.search);
		searchParams.set('timewindow', window);
		searchParams.set('hours', hoursMap[window].toString());
		searchParams.set('granularity', granularityMap[window]);
		goto(`?${searchParams.toString()}`, { replaceState: true });
	}
</script>

<div class="grid grid-cols-1 gap-4 xl:grid-cols-4">
	<!-- Left column: system metrics with the switch-config panel underneath -->
	<div class="flex flex-col gap-4 xl:col-span-3">
		<Section title={$t('device-details.system-metrics')}>
			<div class="mb-4 flex gap-2">
				{#each ['1h', '24h', '7d'] as w (w)}
					<button
						class="ds-btn ds-btn-sm {metricsTimeWindow === w ? 'ds-btn-primary' : ''}"
						onclick={() => handleTimeWindowChange(w as TimeWindow)}
					>
						{w}
					</button>
				{/each}
			</div>
			<SectionMetrics metrics={data.metrics} timewindow={metricsTimeWindow} />
		</Section>

		<SectionSwitchConfig
			{deploymentInfo}
			{config}
			globalState={data.globalState}
			repoStatus={data.repoStatus}
		/>
	</div>

	<!-- Right column: device info, next to the metrics + switch panel -->
	<div class="xl:col-span-1">
		<SectionDeviceInfo bind:deploymentInfo globalState={data.globalState} />
	</div>

	<div class="xl:col-span-2">
		<SectionOnlineStatus connectionHistory={data.connectionHistory} />
	</div>
	<div class="xl:col-span-2">
		<SectionErrorLogs errorLogs={data.errorLogs} />
	</div>
</div>
