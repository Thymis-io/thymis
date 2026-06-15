<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Toggle } from 'flowbite-svelte';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import Page from '$lib/components/layout/Page.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import ActionButton from '$lib/components/layout/ActionButton.svelte';
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

	let hideOldDevices = $state(true);

	// hide after 1 day
	const hideAfter = 1 * 1000 * 60 * 60 * 24; // 1000ms/s * 60s/m * 60m/h * 24h/d = X ms/d = 1 => 1d = X ms

	let hardwareDevicesWithoutDeploymentInfo = $derived(
		data.hardwareDevices.filter((hardwareDevice) => !hardwareDevice.deployment_info_id)
	);

	let visibleDeploymentInfos = $derived(
		data.deploymentInfos.filter(
			(deploymentInfo) =>
				!hideOldDevices ||
				(deploymentInfo.last_seen &&
					new Date(deploymentInfo.last_seen) > new Date(data.loadTime - hideAfter))
		)
	);
</script>

<Page title={$t('nav.devices')} subtitle={$t('hardware-devices.subtitle')}>
	<div class="flex items-center justify-between gap-4 mb-3">
		<h2 class="ds-section-title">{$t('hardware-devices.known-devices-with-deployment')}</h2>
		<div class="flex items-center gap-2">
			<Toggle bind:checked={hideOldDevices} />
			<label for="hideOldDevices" class="text-sm" style="color: var(--ds-text-dim)">
				{$t('hardware-devices.hide-old-devices')}
			</label>
		</div>
	</div>

	<DataTable
		columns={[
			{ label: $t('hardware-devices.table.device') },
			{ label: $t('hardware-devices.table.configuration-name') },
			{ label: $t('hardware-devices.table.deployed-config-commit') },
			{ label: $t('hardware-devices.table.device-type') },
			{ label: $t('hardware-devices.table.hardware-ids') },
			{ label: $t('hardware-devices.table.connected') },
			{}
		]}
		rows={visibleDeploymentInfos}
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
				<IdentifierLink
					identifier={deploymentInfo.id}
					context="device"
					globalState={data.globalState}
					deploymentInfos={data.deploymentInfos}
				/>
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
				{#if isConnected}
					<span class="ds-status-pill online">
						<span class="ds-dot"></span>{$t('hardware-devices.table.connected')}
					</span>
				{:else}
					<span class="ds-status-pill offline">
						<span class="ds-dot"></span>
						{#if timestamp}
							<RenderTimeAgo {timestamp} />
						{:else}
							{$t('hardware-devices.table.never-seen')}
						{/if}
					</span>
				{/if}
			</td>
			<td>
				<ActionButton label={$t('device-details.details')} href={'/devices/' + deploymentInfo.id} />
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
