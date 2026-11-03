<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/state';
	import { invalidate } from '$app/navigation';
	import type { PageData } from './$types';
	import { getDeviceTypesMap, getDeviceType, formatRamSize } from '#lib/config/configUtils.js';
	import DataTable from '#lib/components/layout/DataTable.svelte';
	import FilterChips from '#lib/components/layout/FilterChips.svelte';
	import RowActions from '#lib/components/layout/RowActions.svelte';
	import RowMenu from '#lib/components/layout/RowMenu.svelte';
	import RenderTimeAgo from '#lib/components/RenderTimeAgo.svelte';
	import IdentifierLink from '#lib/IdentifierLink.svelte';
	import { updateDeploymentInfo, type DeploymentInfo } from '#lib/deploymentInfo.js';
	import ArchiveIcon from 'lucide-svelte/icons/archive';
	import DetailsIcon from 'lucide-svelte/icons/info';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import { getHardwareKeyDisplayName } from '#lib/hardwareDevices.js';
	import RebootDevicesModal from '#lib/components/RebootDevicesModal.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let deviceTypes = $derived(getDeviceTypesMap(data.availableModules));

	type StatusFilter = 'all' | 'online' | 'offline' | 'reboot-required';

	const initialStatus = page.url.searchParams.get('status');
	let statusFilter = $state<StatusFilter>(
		initialStatus === 'online' || initialStatus === 'offline' || initialStatus === 'reboot-required'
			? initialStatus
			: 'all'
	);

	let activeDevices = $derived(data.globalState.deploymentInfos.filter((di) => !di.archived));
	let onlineCount = $derived(activeDevices.filter((di) => di.connected).length);
	let rebootRequiredCount = $derived(activeDevices.filter((di) => di.reboot_required).length);

	let visibleDevices = $derived(
		statusFilter === 'online'
			? activeDevices.filter((di) => di.connected)
			: statusFilter === 'offline'
				? activeDevices.filter((di) => !di.connected)
				: statusFilter === 'reboot-required'
					? activeDevices.filter((di) => di.reboot_required)
					: activeDevices
	);

	// Selection is scoped to the visible rows: ids that drop out of view are deselected.
	let selectedIds = $state<string[]>([]);
	$effect(() => {
		const visible = new Set(visibleDevices.map((di) => di.id));
		const kept = selectedIds.filter((id) => visible.has(id));
		if (kept.length !== selectedIds.length) selectedIds = kept;
	});
	let selectedDevices = $derived(visibleDevices.filter((di) => selectedIds.includes(di.id)));

	// Store ids so the modal reflects live connection state while it is open.
	let rebootTargetIds = $state<string[]>([]);
	let rebootTargets = $derived(activeDevices.filter((di) => rebootTargetIds.includes(di.id)));
	let rebootModalOpen = $state(false);
	let rebootingSelection = $state(false);

	function openReboot(targets: DeploymentInfo[], fromSelection: boolean) {
		rebootTargetIds = targets.map((di) => di.id);
		rebootingSelection = fromSelection;
		rebootModalOpen = true;
	}

	async function archiveDevice(id: string) {
		await updateDeploymentInfo(fetch, id, { archived: true });
		await invalidate('/api/all_deployment_infos');
	}
</script>

<div class="flex flex-wrap items-center justify-between gap-x-4">
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
			},
			{
				value: 'reboot-required' as const,
				label: $t('hardware-devices.filter.reboot-required'),
				dot: 'warning' as const,
				count: rebootRequiredCount
			}
		]}
	/>
	{#if selectedDevices.length > 0}
		<div class="mb-[14px] flex items-center gap-2">
			<span class="text-sm" style="color: var(--ds-text-dim)">
				{$t('reboot.selected-count', { values: { count: selectedDevices.length } })}
			</span>
			<button class="ds-btn ds-btn-sm" onclick={() => (selectedIds = [])}>
				{$t('reboot.clear-selection')}
			</button>
			<button
				class="ds-btn ds-btn-sm ds-btn-primary"
				onclick={() => openReboot(selectedDevices, true)}
			>
				<RotateCcw size={'0.875rem'} class="min-w-3.5" />
				{$t('reboot.reboot-selected', { values: { count: selectedDevices.length } })}
			</button>
		</div>
	{/if}
</div>

<DataTable
	columns={[
		{ label: $t('hardware-devices.table.device') },
		{ label: $t('hardware-devices.table.configuration-name') },
		{ label: $t('hardware-devices.table.deployed-config-commit') },
		{ label: $t('hardware-devices.table.device-type') },
		{ label: $t('hardware-devices.table.ram-size') },
		{ label: $t('hardware-devices.table.hardware-ids') },
		{ label: $t('hardware-devices.table.notes') },
		{}
	]}
	rows={visibleDevices}
	rowKey={(di) => di.id}
	selectable
	bind:selected={selectedIds}
	empty={$t('hardware-devices.no-deployed-devices')}
>
	{#snippet row(deploymentInfo)}
		{@const deployedConfig = data.globalState.configs.find(
			(config) => config.identifier === deploymentInfo.deployed_config_id
		)}
		{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
		<td>
			<div class="ds-cell-primary">
				<IdentifierLink
					identifier={deploymentInfo.id}
					context="device"
					globalState={data.globalState}
				/>
				<span class="ds-cell-sub flex items-center gap-1.5">
					<span class="ds-stat-dot {deploymentInfo.connected ? 'online' : 'offline'}"></span>
					{#if deploymentInfo.connected}
						{$t('hardware-devices.table.connected')}
					{:else if deploymentInfo.last_seen}
						{$t('hardware-devices.table.last-seen')}: <RenderTimeAgo
							timestamp={deploymentInfo.last_seen}
						/>
					{:else}
						{$t('hardware-devices.table.never-seen')}
					{/if}
				</span>
				{#if deploymentInfo.reboot_required}
					<span
						class="ds-tag mt-1"
						style="background: var(--ds-warning-dim); color: var(--ds-warning);"
						title={deploymentInfo.reboot_required_reason ??
							$t('device-details.reboot-recommended-hint')}
					>
						{$t('hardware-devices.table.reboot-recommended')}
					</span>
				{/if}
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
		<td>{deploymentInfo.ram_bytes != null ? formatRamSize(deploymentInfo.ram_bytes) : ''}</td>
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
		<td
			class="max-w-96 overflow-hidden whitespace-nowrap text-ellipsis"
			title={deploymentInfo.notes}>{deploymentInfo.notes ?? ''}</td
		>
		<td>
			<RowActions>
				<RowMenu
					label={$t('hardware-devices.actions')}
					items={[
						{
							label: $t('device-details.details'),
							icon: DetailsIcon,
							href: `/devices/${deploymentInfo.id}/details`
						},
						{
							label: $t('reboot.row-action'),
							icon: RotateCcw,
							disabled: !deploymentInfo.connected,
							onclick: () => openReboot([deploymentInfo], false)
						},
						{
							label: $t('hardware-devices.archive-device'),
							icon: ArchiveIcon,
							disabled: deploymentInfo.connected,
							onclick: () => archiveDevice(deploymentInfo.id)
						}
					]}
				/>
			</RowActions>
		</td>
	{/snippet}
</DataTable>

<RebootDevicesModal
	bind:open={rebootModalOpen}
	devices={rebootTargets}
	globalState={data.globalState}
	onRebooted={() => {
		if (rebootingSelection) selectedIds = [];
	}}
/>
