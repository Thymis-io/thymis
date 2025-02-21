<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Table, TableBodyCell, TableHead, TableHeadCell } from 'flowbite-svelte';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { page } from '$app/stores';
	import PageHead from '$lib/components/PageHead.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';

	export let data: PageData;

	$: deviceTypes = getDeviceTypesMap(data.availableModules);

	const hardwareKeyToDisplayName = {
		'pi-serial-number': () => $t('hardware-devices.hardware-keys.pi-serial-number')
	} as Record<string, () => string>;
</script>

<PageHead title={$t('nav.devices')} />
<h1 class="text-2xl font-bold">Currently Deployed</h1>
<!--
We add a "Connected" column, which shows yes if last_seen < 30 seconds ago, and last_seen otherwise.
-->
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
	</TableHead>
	<tbody>
		{#each data.deploymentInfos as deploymentInfo (deploymentInfo.id)}
			{@const deployedConfig = data.state.configs.find(
				(config) => config.identifier === deploymentInfo.deployed_config_id
			)}
			{@const deviceType = deployedConfig && getDeviceType(deployedConfig)}
			<tr
				class="h-12 border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
			>
				<TableBodyCell tdClass="p-2"></TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<a
						href={`/configuration/configuration-details?${buildGlobalNavSearchParam($page.url.search, 'config', deploymentInfo.deployed_config_id)}`}
						class="underline flex items-center gap-2 w-fit"
					>
						<FileCode size={18} />
						{data.state.configs.find(
							(config) => config.identifier === deploymentInfo.deployed_config_id
						)?.displayName}
					</a>
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
					{#if new Date(deploymentInfo.last_seen) > new Date(new Date().getTime() - 30000)}
						<span class="text-green-500">Yes</span>
					{:else}
						Last seen: <RenderTimeAgo timestamp={deploymentInfo.last_seen} />
					{/if}
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>

<h1 class="text-2xl font-bold">Known devices without any current deployment</h1>
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.hardware-ids')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.connected')}</TableHeadCell>
	</TableHead>
	<tbody>
		{#each data.hardwareDevices as hardwareDevice (hardwareDevice.id)}
			{#if !hardwareDevice.deployment_info}
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
						Last seen: <RenderTimeAgo timestamp={hardwareDevice.last_seen} />
					</TableBodyCell>
				</tr>
			{/if}
		{/each}
	</tbody>
</Table>
