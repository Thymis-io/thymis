<script lang="ts">
	import { t } from 'svelte-i18n';
	import { onMount } from 'svelte';
	import { Badge, Button, Input, Modal, Spinner } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import type { PageData } from './$types';
	import {
		getConnectionHistory,
		getDeviceMetrics,
		getErrorLogs,
		updateName
	} from '$lib/deploymentInfo';
	import SectionDeviceInfo from './SectionDeviceInfo.svelte';
	import SectionOnlineStatus from './SectionOnlineStatus.svelte';
	import SectionMetrics from './SectionMetrics.svelte';
	import SectionErrorLogs from './SectionErrorLogs.svelte';
	import Section from './Section.svelte';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $state(data.deploymentInfo);

	type TimeWindow = '1h' | '24h' | '7d';

	let connectionHistory: Array<{ connected_at: string; disconnected_at?: string }> = $state([]);
	let metrics: Array<{
		timestamp: string;
		cpu_percent: number;
		ram_percent: number;
		disk_percent: number;
	}> = $state([]);
	let errorLogs: Array<{
		timestamp: string;
		message: string;
		severity: number;
		syslogtag: string;
	}> = $state([]);
	let metricsTimewindow: TimeWindow = $state('7d');
	let metricsLoading = $state(false);

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

	const hoursMap: Record<TimeWindow, number> = { '1h': 1, '24h': 24, '7d': 168 };
	const granularityMap: Record<TimeWindow, '1min' | '15min' | '1h'> = {
		'1h': '1min',
		'24h': '15min',
		'7d': '1h'
	};

	onMount(async () => {
		[connectionHistory, metrics, errorLogs] = await Promise.all([
			getConnectionHistory(fetch, deploymentInfo.id),
			getDeviceMetrics(fetch, deploymentInfo.id, 168, '1h'),
			getErrorLogs(fetch, deploymentInfo.id)
		]);
	});

	async function handleTimeWindowChange(window: TimeWindow) {
		metricsTimewindow = window;
		metricsLoading = true;
		metrics = await getDeviceMetrics(
			fetch,
			deploymentInfo.id,
			hoursMap[window],
			granularityMap[window]
		);
		metricsLoading = false;
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
							color={metricsTimewindow === w ? 'blue' : 'light'}
							onclick={() => handleTimeWindowChange(w as TimeWindow)}
						>
							{w}
						</Button>
					{/each}
				</div>
				{#if metricsLoading}
					<Spinner />
				{:else}
					<SectionMetrics {metrics} timewindow={metricsTimewindow} />
				{/if}
			</Section>
		</div>

		<!-- Right sidebar: device info -->
		<div class="flex flex-col gap-6">
			<SectionDeviceInfo bind:deploymentInfo globalState={data.globalState} />
		</div>
	</div>

	<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
		<SectionOnlineStatus {connectionHistory} />
		<SectionErrorLogs {errorLogs} />
	</div>
</div>
