<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Modal } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import type { PageData } from './$types';
	import { updateDeploymentInfo, isOnline as checkOnline } from '$lib/deploymentInfo';
	import SectionDeviceInfo from './SectionDeviceInfo.svelte';
	import SectionSwitchConfig from './SectionSwitchConfig.svelte';
	import SectionOnlineStatus from './SectionOnlineStatus.svelte';
	import SectionMetrics from './SectionMetrics.svelte';
	import SectionErrorLogs from './SectionErrorLogs.svelte';
	import Section from '$lib/components/layout/Section.svelte';
	import VncView from '$lib/vnc/VncView.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import CopySSHCommandButton from '$lib/terminal/CopySSHCommandButton.svelte';
	import LogsView from '$lib/components/LogsView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import ListCollapse from 'lucide-svelte/icons/list-collapse';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import TerminalIcon from 'lucide-svelte/icons/terminal';
	import FileText from 'lucide-svelte/icons/file-text';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
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

	// the configuration this device last deployed, used for the VNC password / gating
	let config = $derived(
		data.globalState.configs.find((c) => c.identifier === deploymentInfo.deployed_config_id)
	);

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

	// Top-level tabs: Details holds the page content; VNC / Terminal / Logs are
	// dedicated views. VNC only appears when the config provides a VNC module.
	type DeviceTab = 'details' | 'vnc' | 'terminal' | 'logs';
	let hasVnc = $derived(!!config && targetShouldShowVNC(config, data.globalState));
	let deviceTabs = $derived([
		{ id: 'details', icon: ListCollapse, labelKey: 'nav.device-details' },
		...(hasVnc ? [{ id: 'vnc', icon: ScreenShare, labelKey: 'nav.device-vnc' }] : []),
		{ id: 'terminal', icon: TerminalIcon, labelKey: 'nav.terminal' },
		{ id: 'logs', icon: FileText, labelKey: 'nav.logs' }
	] as { id: DeviceTab; icon: any; labelKey: string }[]);
	let selectedTab = $state<DeviceTab>('details');
	let activeTab = $derived(
		deviceTabs.some((tab) => tab.id === selectedTab) ? selectedTab : 'details'
	);

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

	const restartDevice = async () => {
		if (!config) return;
		await fetchWithNotify(`/api/action/restart-device?identifier=${config.identifier}`, {
			method: 'POST'
		});
	};

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

	{#snippet actions()}
		{#if config}
			<button class="ds-btn" onclick={restartDevice}>
				<RotateCcw size={'1rem'} class="min-w-4" />
				<span class="whitespace-nowrap">{$t('configurations.actions.restart')}</span>
			</button>
		{/if}
	{/snippet}
</PageHead>

<Modal bind:open={nameModalOpen} title={$t('device-details.edit')}>
	<Input bind:value={nameInput} placeholder={$t('device-details.name-placeholder')} />
	<p class="mt-2 text-xs" style="color: var(--ds-text-mute)">{$t('device-details.name-helper')}</p>
	<div class="mt-4 flex justify-end gap-2">
		<button class="ds-btn" onclick={() => (nameModalOpen = false)}>{$t('common.cancel')}</button>
		<button class="ds-btn ds-btn-primary" onclick={saveName}>{$t('device-details.save')}</button>
	</div>
</Modal>

<div class="mb-4 flex flex-wrap gap-1 border-b border-[var(--ds-border)]" role="tablist">
	{#each deviceTabs as tab (tab.id)}
		<button
			type="button"
			role="tab"
			aria-selected={activeTab === tab.id}
			class="-mb-px border-b-2 p-2 px-3 text-center text-sm font-medium {activeTab === tab.id
				? 'border-[var(--ds-accent)] text-[var(--ds-accent-strong)]'
				: 'border-transparent text-[var(--ds-text-dim)] hover:text-[var(--ds-text)]'}"
			onclick={() => (selectedTab = tab.id)}
		>
			<div class="flex items-center gap-2 px-1 font-semibold md:min-w-32 xl:min-w-48">
				<tab.icon size={18} />
				<span>{$t(tab.labelKey)}</span>
			</div>
		</button>
	{/each}
</div>

{#if activeTab === 'details'}
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
				repoStatus={page.data.repoStatus}
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
{:else if activeTab === 'vnc'}
	<Section title={$t('nav.device-vnc')}>
		{#if data.connected && hasVnc && config}
			<VncView globalState={data.globalState} {config} {deploymentInfo} embedded />
		{:else}
			<p class="tab-empty">{$t('device-details.not-connected')}</p>
		{/if}
	</Section>
{:else if activeTab === 'terminal'}
	<Section title={$t('nav.terminal')}>
		{#snippet header()}
			{#if data.connected}
				<CopySSHCommandButton {deploymentInfo} />
			{/if}
		{/snippet}
		{#if data.connected}
			<Terminal {deploymentInfo} />
		{:else}
			<p class="tab-empty">{$t('device-details.not-connected')}</p>
		{/if}
	</Section>
{:else if activeTab === 'logs'}
	<LogsView
		globalState={data.globalState}
		logs={data.logs}
		programNames={data.programNames}
		deploymentInfos={[deploymentInfo]}
		connectedDeploymentInfos={data.connected ? [deploymentInfo] : []}
		selectedDeploymentInfoId={deploymentInfo.id}
		showSelector={false}
	/>
{/if}

<style lang="postcss">
	.tab-empty {
		padding: 24px 4px;
		font-size: 14px;
		color: var(--ds-text-mute);
	}
</style>
