<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Table, TableBodyCell, TableHead, TableHeadCell } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import { page } from '$app/stores';
	import EditDeploymentInfo from '$lib/EditDeploymentInfo.svelte';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import PageHead from '$lib/components/PageHead.svelte';

	export let data: PageData;

	$: hardwareDevices = data.hardwareDevices.map((device) => ({
		id: device.id,
		hardwareDevice: device
	}));

	$: deviceTypes = getDeviceTypesMap(data.availableModules);

	let editDeploymentInfoModalOpen = false;
	let currentDeploymentInfo: DeploymentInfo | undefined = undefined;

	const hardwareKeyToDisplayName = {
		'pi-serial-number': () => $t('hardware-devices.hardware-keys.pi-serial-number')
	} as Record<string, () => string>;
</script>

<PageHead title={$t('nav.hardware-devices')} />
<EditDeploymentInfo
	bind:deploymentInfo={currentDeploymentInfo}
	bind:open={editDeploymentInfoModalOpen}
	configIdentifier={currentDeploymentInfo?.deployed_config_id ?? undefined}
/>
<Table shadow>
	<TableHead theadClass="text-xs normal-case">
		<TableHeadCell padding="p-2 w-12" />
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.configuration-name')}</TableHeadCell>
		<TableHeadCell padding="p-2">
			{$t('hardware-devices.table.deployed-config-commit')}
		</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.device-type')}</TableHeadCell>
		<TableHeadCell padding="p-2">{$t('hardware-devices.table.hardware-ids')}</TableHeadCell>
	</TableHead>
	<tbody>
		{#each hardwareDevices as { id, hardwareDevice }, i (id)}
			{@const deployedConfig = data.state.configs.find(
				(config) => config.identifier === hardwareDevice.deployment_info?.deployed_config_id
			)}
			{@const deviceType = getDeviceType(deployedConfig)}
			<tr
				class="h-12 border-b last:border-b-0 bg-white dark:bg-gray-800 dark:border-gray-700 whitespace-nowrap"
			>
				<TableBodyCell tdClass="p-2"></TableBodyCell>
				<TableBodyCell tdClass="p-2">
					<a
						href={`/configuration/configuration-details?${buildGlobalNavSearchParam($page.url.search, 'config', deployedConfig?.identifier)}`}
						class="underline flex items-center gap-2 w-fit"
					>
						<FileCode size={18} />
						{deployedConfig?.displayName}
					</a>
				</TableBodyCell>
				{#if hardwareDevice.deployment_info?.deployed_config_commit}
					<TableBodyCell tdClass="p-2">
						<span class="playwright-snapshot-unstable font-mono">
							{hardwareDevice.deployment_info.deployed_config_commit.slice(0, 8)}
						</span>
					</TableBodyCell>
				{:else}
					<TableBodyCell tdClass="p-2">{$t('configuration-details.no-commit')}</TableBodyCell>
				{/if}
				<TableBodyCell tdClass="p-2">
					{deviceType && deviceType in deviceTypes ? deviceTypes[deviceType] : deviceType}
				</TableBodyCell>
				<TableBodyCell tdClass="p-2">
					{#each Object.entries(hardwareDevice.hardware_ids) as [hardwareIdKey, hardwareValue]}
						<div class="flex gap-2">
							{hardwareIdKey in hardwareKeyToDisplayName
								? hardwareKeyToDisplayName[hardwareIdKey]()
								: hardwareIdKey}: {hardwareValue}
						</div>
					{/each}
				</TableBodyCell>
			</tr>
		{/each}
	</tbody>
</Table>
