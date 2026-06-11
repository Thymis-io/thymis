<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Modal } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import type { PageData } from './$types';
	import { updateDeploymentInfo, isOnline as checkOnline } from '$lib/deploymentInfo';
	import SectionDeviceInfo from './SectionDeviceInfo.svelte';
	import SectionOnlineStatus from './SectionOnlineStatus.svelte';
	import SectionMetrics from './SectionMetrics.svelte';
	import SectionErrorLogs from './SectionErrorLogs.svelte';
	import Section from './Section.svelte';
	import { page } from '$app/state';
	import { goto, invalidate } from '$app/navigation';
	import { queryParameters } from 'sveltekit-search-params';
	import PageHead from '$lib/components/layout/PageHead.svelte';

	const params = queryParameters();

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $derived(data.deploymentInfo);

	type TimeWindow = '1h' | '24h' | '7d';

	let metricsTimeWindow: TimeWindow = $derived.by(() => {
		const tw = params['timewindow'];
		if (tw === '1h' || tw === '24h' || tw === '7d') {
			return tw;
		}
		return '24h';
	});

	let nameModalOpen = $state(false);
	let nameInput = $state('');

	let isOnline = $derived(checkOnline(deploymentInfo.last_seen));

	function openNameModal() {
		nameInput = deploymentInfo.name ?? '';
		nameModalOpen = true;
	}

	async function saveName() {
		const response = await updateDeploymentInfo(fetch, deploymentInfo.id, {
			name: nameInput || null
		});
		if (response.ok) {
			nameModalOpen = false;
			await invalidate(`/api/deployment_info/${deploymentInfo.id}`);
		}
	}

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

<PageHead
	title={deploymentInfo.name ?? deploymentInfo.id}
	subtitle={deploymentInfo.reachable_deployed_host ?? undefined}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
	selectedDeploymentInfo={deploymentInfo}
>
	<button
		onclick={openNameModal}
		class="rounded p-1"
		style="color: var(--ds-text-mute)"
		title={$t('device-details.edit')}
	>
		<Pen class="h-[18px] w-[18px]" />
	</button>
	<span class="ds-status-pill {isOnline ? 'online' : 'offline'}">
		<span class="ds-dot"></span>
		{isOnline ? $t('device-details.online') : $t('device-details.offline')}
	</span>
</PageHead>

<Modal bind:open={nameModalOpen} title={$t('device-details.edit')}>
	<Input bind:value={nameInput} placeholder={$t('device-details.name-placeholder')} />
	<div class="mt-4 flex justify-end gap-2">
		<button class="ds-btn" onclick={() => (nameModalOpen = false)}>{$t('common.cancel')}</button>
		<button class="ds-btn ds-btn-primary" onclick={saveName}>{$t('device-details.save')}</button>
	</div>
</Modal>

<div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
	<!-- System metrics: 3/4 width -->
	<div class="lg:col-span-3">
		<Section title={$t('device-details.system-metrics')} class="h-full">
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
	</div>

	<!-- Right sidebar: device info -->
	<div class="flex flex-col gap-6 h-full">
		<SectionDeviceInfo bind:deploymentInfo globalState={data.globalState} />
	</div>

	<div class="lg:col-span-2">
		<SectionOnlineStatus connectionHistory={data.connectionHistory} />
	</div>
	<div class="lg:col-span-2">
		<SectionErrorLogs errorLogs={data.errorLogs} />
	</div>
</div>
