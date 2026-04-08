<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Badge, Button, Input, Modal, Spinner } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import type { PageData } from './$types';
	import { updateName } from '$lib/deploymentInfo';
	import SectionDeviceInfo from './SectionDeviceInfo.svelte';
	import SectionOnlineStatus from './SectionOnlineStatus.svelte';
	import SectionMetrics from './SectionMetrics.svelte';
	import SectionErrorLogs from './SectionErrorLogs.svelte';
	import Section from './Section.svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { queryParameters } from 'sveltekit-search-params';

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

	const ONLINE_THRESHOLD_MS = 30 * 1000;
	let isOnline = $derived(
		!!deploymentInfo.last_seen &&
			Date.now() - new Date(deploymentInfo.last_seen).getTime() < ONLINE_THRESHOLD_MS
	);

	function openNameModal() {
		nameInput = deploymentInfo.name ?? '';
		nameModalOpen = true;
	}

	async function saveName() {
		const response = await updateName(fetch, deploymentInfo.id, nameInput || null);
		if (response.ok) {
			deploymentInfo = { ...deploymentInfo, name: nameInput || null };
			nameModalOpen = false;
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

<div class="space-y-6 p-6">
	<header class="flex items-center gap-3">
		<div>
			<div class="flex items-center gap-2">
				<h1 class="text-3xl font-bold">{deploymentInfo.name ?? deploymentInfo.id}</h1>
				<Badge color={isOnline ? 'green' : 'red'}>
					{isOnline ? $t('device-details.online') : $t('device-details.offline')}
				</Badge>
			</div>
			{#if deploymentInfo.name}
				<p class="mt-1 font-mono text-sm text-gray-500">{deploymentInfo.id}</p>
			{/if}
		</div>
		<button
			onclick={openNameModal}
			class="rounded p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
			title={$t('device-details.edit')}
		>
			<Pen class="h-5 w-5" />
		</button>
	</header>

	<Modal bind:open={nameModalOpen} title={$t('device-details.edit')}>
		<Input bind:value={nameInput} placeholder={$t('device-details.name-placeholder')} />
		<div class="mt-4 flex gap-2">
			<Button onclick={saveName}>{$t('device-details.save')}</Button>
			<Button color="light" onclick={() => (nameModalOpen = false)}>{$t('common.cancel')}</Button>
		</div>
	</Modal>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-4">
		<!-- System metrics: 3/4 width -->
		<div class="lg:col-span-3">
			<Section title={$t('device-details.system-metrics')} class="h-full">
				<div class="mb-4 flex gap-2">
					{#each ['1h', '24h', '7d'] as w (w)}
						<Button
							color={metricsTimeWindow === w ? 'blue' : 'light'}
							onclick={() => handleTimeWindowChange(w as TimeWindow)}
						>
							{w}
						</Button>
					{/each}
				</div>
				<SectionMetrics metrics={data.metrics} timewindow={metricsTimeWindow} />
			</Section>
		</div>

		<!-- Right sidebar: device info -->
		<div class="flex flex-col gap-6">
			<SectionDeviceInfo bind:deploymentInfo globalState={data.globalState} />
		</div>
	</div>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<SectionOnlineStatus connectionHistory={data.connectionHistory} />
		<SectionErrorLogs errorLogs={data.errorLogs} />
	</div>
</div>
