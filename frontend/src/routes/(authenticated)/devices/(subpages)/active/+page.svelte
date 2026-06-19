<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/state';
	import { invalidate } from '$app/navigation';
	import type { PageData } from './$types';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import FilterChips from '$lib/components/layout/FilterChips.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import RowMenu from '$lib/components/layout/RowMenu.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import { isOnline, updateDeploymentInfo } from '$lib/deploymentInfo';
	import ArchiveIcon from 'lucide-svelte/icons/archive';
	import { getHardwareKeyDisplayName } from '$lib/hardwareDevices';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let deviceTypes = $derived(getDeviceTypesMap(data.availableModules));

	type StatusFilter = 'all' | 'online' | 'offline';

	const initialStatus = page.url.searchParams.get('status');
	let statusFilter = $state<StatusFilter>(
		initialStatus === 'online' || initialStatus === 'offline' ? initialStatus : 'all'
	);

	let activeDevices = $derived(data.deploymentInfos.filter((di) => !di.archived));
	let onlineCount = $derived(activeDevices.filter((di) => isOnline(di.last_seen)).length);

	let visibleDevices = $derived(
		statusFilter === 'online'
			? activeDevices.filter((di) => isOnline(di.last_seen))
			: statusFilter === 'offline'
				? activeDevices.filter((di) => !isOnline(di.last_seen))
				: activeDevices
	);

	async function archiveDevice(id: string) {
		await updateDeploymentInfo(fetch, id, { archived: true });
		await invalidate('/api/all_deployment_infos');
	}
</script>

<FilterChips
	bind:selected={statusFilter}
	chips={[
		{
			value: 'all' as const,
			label: $t('hardware-devices.filter.all'),
			count: activeDevices.length
		},
		{
			value: 'online' as const,
			label: $t('hardware-devices.filter.online'),
			dot: 'online' as const,
			count: onlineCount
		},
		{
			value: 'offline' as const,
			label: $t('hardware-devices.filter.offline'),
			dot: 'offline' as const,
			count: activeDevices.length - onlineCount
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
	rows={visibleDevices}
	empty={$t('hardware-devices.no-deployed-devices')}
>
	{#snippet row(deploymentInfo)}
		{@const deployedConfig = data.globalState.configs.find(
			(config) => config.identifier === deploymentInfo.deployed_config_id
		)}
		{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
		{@const isConnected = isOnline(deploymentInfo.last_seen)}
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
					{:else if deploymentInfo.last_seen}
						{$t('hardware-devices.table.last-seen')}: <RenderTimeAgo
							timestamp={deploymentInfo.last_seen}
						/>
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
						{getHardwareKeyDisplayName(hardwareIdKey)}: {hardwareValue}
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
					items={[
						{
							label: $t('device-details.details'),
							href: `/devices/${deploymentInfo.id}/details`
						},
						{
							label: $t('hardware-devices.archive-device'),
							icon: ArchiveIcon,
							disabled: isOnline(deploymentInfo.last_seen),
							onclick: () => archiveDevice(deploymentInfo.id)
						}
					]}
				/>
			</RowActions>
		</td>
	{/snippet}
</DataTable>
