<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Toggle } from 'flowbite-svelte';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import PageHead from '$lib/components/layout/PageHead.svelte';
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
</script>

<PageHead
	title={$t('nav.devices')}
	subtitle={$t('hardware-devices.subtitle')}
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>

<div class="flex items-center justify-between gap-4 mb-3">
	<h2 class="ds-section-title">{$t('hardware-devices.known-devices-with-deployment')}</h2>
	<div class="flex items-center gap-2">
		<Toggle bind:checked={hideOldDevices} />
		<label for="hideOldDevices" class="text-sm" style="color: var(--ds-text-dim)">
			{$t('hardware-devices.hide-old-devices')}
		</label>
	</div>
</div>

<div class="ds-table-wrap">
	<table class="ds-table">
		<thead>
			<tr>
				<th>{$t('hardware-devices.table.device')}</th>
				<th>{$t('hardware-devices.table.configuration-name')}</th>
				<th>{$t('hardware-devices.table.deployed-config-commit')}</th>
				<th>{$t('hardware-devices.table.device-type')}</th>
				<th>{$t('hardware-devices.table.hardware-ids')}</th>
				<th>{$t('hardware-devices.table.connected')}</th>
				<th></th>
			</tr>
		</thead>
		<tbody>
			{#each data.deploymentInfos as deploymentInfo (deploymentInfo.id)}
				{#if !hideOldDevices || (deploymentInfo.last_seen && new Date(deploymentInfo.last_seen) > new Date(data.loadTime - hideAfter))}
					{@const deployedConfig = data.globalState.configs.find(
						(config) => config.identifier === deploymentInfo.deployed_config_id
					)}
					{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
					{@const timestamp = deploymentInfo?.last_seen}
					{@const isConnected =
						!!timestamp && new Date(timestamp) > new Date(new Date().getTime() - 30000)}
					<tr>
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
								<span style="color: var(--ds-text-mute)"
									>{$t('configuration-details.no-commit')}</span
								>
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
							<a class="ds-btn ds-btn-sm" href={'/devices/' + deploymentInfo.id}>
								{$t('device-details.details')}
							</a>
						</td>
					</tr>
				{/if}
			{/each}
		</tbody>
	</table>
</div>

<h2 class="ds-section-title mt-7 mb-3">
	{$t('hardware-devices.known-devices-without-deployment')}
</h2>
{#if hardwareDevicesWithoutDeploymentInfo.length === 0}
	<div class="ds-table-wrap ds-table-empty">
		{$t('hardware-devices.no-known-hardware-devices-without-known-deployment')}
	</div>
{:else}
	<div class="ds-table-wrap">
		<table class="ds-table">
			<thead>
				<tr>
					<th>{$t('hardware-devices.table.hardware-ids')}</th>
					<th>{$t('hardware-devices.table.last-seen')}</th>
				</tr>
			</thead>
			<tbody>
				{#each hardwareDevicesWithoutDeploymentInfo as hardwareDevice (hardwareDevice.id)}
					<tr>
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
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
{/if}
