<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import Page from '$lib/components/layout/Page.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import FilterChips from '$lib/components/layout/FilterChips.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import RowMenu from '$lib/components/layout/RowMenu.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let deviceTypes = $derived(getDeviceTypesMap(data.availableModules));

	const hardwareKeyToDisplayName = {
		'pi-serial-number': () => $t('hardware-devices.hardware-keys.pi-serial-number')
	} as Record<string, () => string>;

	// A device counts as online when it was last seen within the last 30 seconds.
	const connectedWindowMs = 30000;
	const isOnline = (deploymentInfo: { last_seen?: string | null }) =>
		!!deploymentInfo.last_seen &&
		new Date(deploymentInfo.last_seen).getTime() > data.loadTime - connectedWindowMs;

	let statusFilter = $state<'all' | 'online' | 'offline'>('all');

	let onlineCount = $derived(data.deploymentInfos.filter(isOnline).length);

	let hardwareDevicesWithoutDeploymentInfo = $derived(
		data.hardwareDevices.filter((hardwareDevice) => !hardwareDevice.deployment_info_id)
	);

	let visibleDeploymentInfos = $derived(
		statusFilter === 'online'
			? data.deploymentInfos.filter(isOnline)
			: statusFilter === 'offline'
				? data.deploymentInfos.filter((deploymentInfo) => !isOnline(deploymentInfo))
				: data.deploymentInfos
	);
</script>

<Page title={$t('nav.devices')} subtitle={$t('hardware-devices.subtitle')}>
	<h2 class="ds-section-title mb-3">{$t('hardware-devices.known-devices-with-deployment')}</h2>

	<FilterChips
		bind:selected={statusFilter}
		chips={[
			{
				value: 'all',
				label: $t('hardware-devices.filter.all'),
				count: data.deploymentInfos.length
			},
			{
				value: 'online',
				label: $t('hardware-devices.filter.online'),
				dot: 'online',
				count: onlineCount
			},
			{
				value: 'offline',
				label: $t('hardware-devices.filter.offline'),
				dot: 'offline',
				count: data.deploymentInfos.length - onlineCount
			}
		]}
	/>

	<DataTable
		columns={[
			{ label: $t('hardware-devices.table.device') },
			{ label: $t('hardware-devices.table.configuration-name') },
			{ label: $t('hardware-devices.table.deployed-config-commit') },
			{ label: $t('hardware-devices.table.device-type') },
			{ label: $t('hardware-devices.table.hardware-ids') },
			{}
		]}
		rows={visibleDeploymentInfos}
		empty={$t('hardware-devices.no-deployed-devices')}
	>
		{#snippet row(deploymentInfo)}
			{@const deployedConfig = data.globalState.configs.find(
				(config) => config.identifier === deploymentInfo.deployed_config_id
			)}
			{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
			{@const timestamp = deploymentInfo?.last_seen}
			{@const isConnected =
				!!timestamp && new Date(timestamp) > new Date(new Date().getTime() - 30000)}
			<td>
				<div class="ds-cell-primary">
					<IdentifierLink
						identifier={deploymentInfo.id}
						context="device"
						globalState={data.globalState}
						deploymentInfos={data.deploymentInfos}
					/>
					<span class="ds-cell-sub flex items-center gap-1.5">
						<span class="ds-stat-dot {isConnected ? 'online' : 'offline'}"></span>
						{#if isConnected}
							{$t('hardware-devices.table.connected')}
						{:else if timestamp}
							{$t('hardware-devices.table.last-seen')}: <RenderTimeAgo {timestamp} />
						{:else}
							{$t('hardware-devices.table.never-seen')}
						{/if}
					</span>
				</div>
			</td>
			<td>
				<IdentifierLink
					identifier={deploymentInfo.deployed_config_id}
					context="config"
					globalState={data.globalState}
				/>
			</td>
			<td>
				{#if deploymentInfo.deployed_config_commit}
					<span class="playwright-snapshot-unstable ds-mono">
						{deploymentInfo.deployed_config_commit.slice(0, 8)}
					</span>
				{:else}
					<span style="color: var(--ds-text-mute)">{$t('configuration-details.no-commit')}</span>
				{/if}
			</td>
			<td>
				{#if deployedConfig}
					<span class="ds-tag">
						{deviceType && deviceType in deviceTypes ? deviceTypes[deviceType] : deviceType}
					</span>
				{:else}
					<span style="color: var(--ds-text-mute)"
						>{$t('hardware-devices.table.unknown-device-type')}</span
					>
				{/if}
			</td>
			<td>
				{#if deploymentInfo.hardware_devices.length === 1}
					{#each Object.entries(deploymentInfo.hardware_devices[0].hardware_ids) as [hardwareIdKey, hardwareValue]}
						<div class="ds-mono">
							{hardwareIdKey in hardwareKeyToDisplayName
								? hardwareKeyToDisplayName[hardwareIdKey]()
								: hardwareIdKey}: {hardwareValue}
						</div>
					{/each}
				{:else}
					<span style="color: var(--ds-text-mute)"
						>{$t('hardware-devices.table.no-hardware-ids')}</span
					>
				{/if}
			</td>
			<td>
				<RowActions>
					<RowMenu
						label={$t('hardware-devices.actions')}
						items={[{ label: $t('device-details.details'), href: '/devices/' + deploymentInfo.id }]}
					/>
				</RowActions>
			</td>
		{/snippet}
	</DataTable>

	<div class="mt-7 mb-3">
		<h2 class="ds-section-title">
			{$t('hardware-devices.known-devices-without-deployment')}
		</h2>
	</div>
	<DataTable
		columns={[
			{ label: $t('hardware-devices.table.hardware-ids') },
			{ label: $t('hardware-devices.table.last-seen') }
		]}
		rows={hardwareDevicesWithoutDeploymentInfo}
		empty={$t('hardware-devices.no-known-hardware-devices-without-known-deployment')}
	>
		{#snippet row(hardwareDevice)}
			<td>
				{#each Object.entries(hardwareDevice.hardware_ids) as [hardwareIdKey, hardwareValue]}
					<div class="ds-mono">
						{hardwareIdKey in hardwareKeyToDisplayName
							? hardwareKeyToDisplayName[hardwareIdKey]()
							: hardwareIdKey}: {hardwareValue}
					</div>
				{/each}
			</td>
			<td>
				<RenderTimeAgo timestamp={hardwareDevice.last_seen} />
			</td>
		{/snippet}
	</DataTable>
</Page>
