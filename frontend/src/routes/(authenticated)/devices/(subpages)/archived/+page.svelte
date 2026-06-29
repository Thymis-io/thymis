<script lang="ts">
	import { t } from 'svelte-i18n';
	import { invalidate } from '$app/navigation';
	import type { PageData } from './$types';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import RowMenu from '$lib/components/layout/RowMenu.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import { updateDeploymentInfo } from '$lib/deploymentInfo';
	import ArchiveRestore from 'lucide-svelte/icons/archive-restore';
	import DetailsIcon from 'lucide-svelte/icons/info';
	import { getHardwareKeyDisplayName } from '$lib/hardwareDevices';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let deviceTypes = $derived(getDeviceTypesMap(data.availableModules));

	let archivedDevices = $derived(data.globalState.deploymentInfos.filter((di) => di.archived));

	async function restoreDevice(id: string) {
		await updateDeploymentInfo(fetch, id, { archived: false });
		await invalidate('/api/all_deployment_infos');
	}
</script>

<DataTable
	columns={[
		{ label: $t('hardware-devices.table.device') },
		{ label: $t('hardware-devices.table.configuration-name') },
		{ label: $t('hardware-devices.table.deployed-config-commit') },
		{ label: $t('hardware-devices.table.device-type') },
		{ label: $t('hardware-devices.table.hardware-ids') },
		{}
	]}
	rows={archivedDevices}
	empty={$t('hardware-devices.no-archived-devices')}
>
	{#snippet row(deploymentInfo)}
		{@const deployedConfig = data.globalState.configs.find(
			(config) => config.identifier === deploymentInfo.deployed_config_id
		)}
		{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
		<td>
			<div class="ds-cell-primary">
				<IdentifierLink
					globalState={data.globalState}
					identifier={deploymentInfo.id}
					context="device"
				/>
				<span class="ds-cell-sub flex items-center gap-1.5">
					<span class="ds-stat-dot {deploymentInfo.connected ? 'online' : 'offline'}"></span>
					{#if deploymentInfo.last_seen}
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
				globalState={data.globalState}
				identifier={deploymentInfo.deployed_config_id}
				context="config"
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
				<span style="color: var(--ds-text-mute)">
					{$t('hardware-devices.table.unknown-device-type')}
				</span>
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
					menuWidth={280}
					items={[
						{
							label: $t('device-details.details'),
							icon: DetailsIcon,
							href: `/devices/${deploymentInfo.id}/details`
						},
						{
							label: $t('hardware-devices.unarchive-device'),
							icon: ArchiveRestore,
							onclick: () => restoreDevice(deploymentInfo.id)
						}
					]}
				/>
			</RowActions>
		</td>
	{/snippet}
</DataTable>
