<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Button, Table, TableBodyCell, TableHead, TableHeadCell, Toggle } from 'flowbite-svelte';
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
	repoStatus={data.repoStatus}
	globalState={data.globalState}
	nav={data.nav}
/>
<!-- Add show all devices slider checkbox -->
<div class="flex items-center justify-between mb-4">
	<h1 class="text-2xl font-bold">{$t('hardware-devices.known-devices-with-deployment')}</h1>
	<div class="flex items-center gap-2">
		<Toggle bind:checked={hideOldDevices} />
		<label for="hideOldDevices">{$t('hardware-devices.hide-old-devices')}</label>
	</div>
</div>
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.configuration-name')}</TableHeadCell>
		<TableHeadCell padding="p-2">
			{$t('hardware-devices.table.deployed-config-commit')}
		</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.device-type')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.hardware-ids')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.connected')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.actions')}</TableHeadCell>
	</TableHead>
	<tbody>
		{#each data.deploymentInfos as deploymentInfo (deploymentInfo.id)}
			{#if !hideOldDevices || (deploymentInfo.last_seen && new Date(deploymentInfo.last_seen) > new Date(data.loadTime - hideAfter))}
				{@const deployedConfig = data.globalState.configs.find(
					(config) => config.identifier === deploymentInfo.deployed_config_id
				)}
				{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
				<tr
					class="h-12 border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
				>
					<TableBodyCell tdClass="p-2"></TableBodyCell>
					<TableBodyCell tdClass="p-2">
						<IdentifierLink
							identifier={deploymentInfo.deployed_config_id}
							context="config"
							globalState={data.globalState}
						/>
					</TableBodyCell>
					<TableBodyCell tdClass="p-2">
						{#if deploymentInfo.deployed_config_commit}
							<span class="playwright-snapshot-unstable font-mono">
								{deploymentInfo.deployed_config_commit.slice(0, 8)}
							</span>
						{:else}
							<span>{$t('configuration-details.no-commit')}</span>
						{/if}
					</TableBodyCell>
					<TableBodyCell tdClass="p-2">
						{#if deployedConfig}
							{deviceType && deviceType in deviceTypes ? deviceTypes[deviceType] : deviceType}
						{:else}
							<span>{$t('hardware-devices.table.unknown-device-type')}</span>
						{/if}
					</TableBodyCell>
					<TableBodyCell tdClass="p-2">
						{#if deploymentInfo.hardware_devices.length === 1}
							{#each Object.entries(deploymentInfo.hardware_devices[0].hardware_ids) as [hardwareIdKey, hardwareValue]}
								<div class="flex gap-2">
									{hardwareIdKey in hardwareKeyToDisplayName
										? hardwareKeyToDisplayName[hardwareIdKey]()
										: hardwareIdKey}: {hardwareValue}
								</div>
							{/each}
						{:else}
							<span>{$t('hardware-devices.table.no-hardware-ids')}</span>
						{/if}
					</TableBodyCell>
					<TableBodyCell tdClass="p-2">
						{@const timestamp =
							deploymentInfo &&
							deploymentInfo.last_seen &&
							(deploymentInfo.last_seen.includes('+')
								? deploymentInfo.last_seen
								: deploymentInfo.last_seen + '+0000')}
						{#if timestamp && new Date(timestamp) > new Date(new Date().getTime() - 30000)}
							<span class="text-green-500">{$t('hardware-devices.table.connected')}</span>
						{:else}
							{$t('hardware-devices.table.last-seen')}: {#if timestamp}
								<RenderTimeAgo {timestamp} />
							{:else}
								<span>{$t('hardware-devices.table.never-seen')}</span>
							{/if}
						{/if}
					</TableBodyCell>
					<TableBodyCell tdClass="p-2">
						<!-- View Logs button -->
						<a href={`/deployment_info/${deploymentInfo.id}/logs`}>
							<Button>
								{$t('hardware-devices.table.view-logs')}
							</Button>
						</a>
					</TableBodyCell>
				</tr>
			{/if}
		{/each}
	</tbody>
</Table>

<h1 class="mt-6 text-2xl font-bold">{$t('hardware-devices.known-devices-without-deployment')}</h1>
{#if hardwareDevicesWithoutDeploymentInfo.length === 0}
	<p>{$t('hardware-devices.no-known-hardware-devices-without-known-deployment')}</p>
{:else}
	<Table shadow>
		<TableHead theadClass="text-xs normal-case">
			<TableHeadCell padding="p-2 w-12" />
			<TableHeadCell padding="p-2">{$t('hardware-devices.table.hardware-ids')}</TableHeadCell>
			<TableHeadCell padding="p-2">{$t('hardware-devices.table.last-seen')}</TableHeadCell>
		</TableHead>
		<tbody>
			{#each hardwareDevicesWithoutDeploymentInfo as hardwareDevice (hardwareDevice.id)}
				<tr
					class="h-12 border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
				>
					<TableBodyCell tdClass="p-2"></TableBodyCell>
					<TableBodyCell tdClass="p-2">
						{#each Object.entries(hardwareDevice.hardware_ids) as [hardwareIdKey, hardwareValue]}
							<div class="flex gap-2">
								{hardwareIdKey in hardwareKeyToDisplayName
									? hardwareKeyToDisplayName[hardwareIdKey]()
									: hardwareIdKey}: {hardwareValue}
							</div>
						{/each}
					</TableBodyCell>
					<TableBodyCell tdClass="p-2">
						<RenderTimeAgo timestamp={hardwareDevice.last_seen} />
					</TableBodyCell>
				</tr>
			{/each}
		</tbody>
	</Table>
{/if}
