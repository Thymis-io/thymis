<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import {
		Card,
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import ArrowLeft from 'lucide-svelte/icons/arrow-left';
	import { getDeviceTypesMap, getDeviceType } from '$lib/config/configUtils';
	import { page } from '$app/stores';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import { buildGlobalNavSearchParam } from '$lib/searchParamHelpers';
	import Section from '../../configuration/(subpages)/configuration-details/Section.svelte';
	import VncView from '$lib/vnc/VncView.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const hardwareKeyToDisplayName = {
		'pi-serial-number': () => $t('hardware-devices.hardware-keys.pi-serial-number')
	} as Record<string, () => string>;

	let deviceTypes = $derived(getDeviceTypesMap(data.data?.availableModules || []));
</script>

<PageHead
	title={$t('nav.device-details')}
	repoStatus={data.data?.repoStatus}
	globalState={data.data?.globalState}
	nav={data.data?.nav}
/>

<div class="mb-4">
	<a href="/devices" class="flex items-center gap-2 text-primary-600 hover:underline">
		<ArrowLeft size={18} />
		{$t('hardware-devices.back-to-list')}
	</a>
</div>

{#if data.device}
	<div class="grid grid-cols-4 grid-flow-row gap-x-2 gap-y-6">
		<!-- Device information section -->
		<Section class="col-span-3" title={$t('hardware-devices.device-information')}>
			<Card class="w-full max-w-none">
				<Table shadow>
					<TableHead theadClass="text-xs normal-case">
						<TableHeadCell padding="p-2">{$t('hardware-devices.table.property')}</TableHeadCell>
						<TableHeadCell padding="p-2">{$t('hardware-devices.table.value')}</TableHeadCell>
					</TableHead>
					<TableBody>
						<TableBodyRow>
							<TableBodyCell tdClass="p-2 font-medium"
								>{$t('hardware-devices.table.id')}</TableBodyCell
							>
							<TableBodyCell tdClass="p-2">
								<span class="font-mono">{data.device.id}</span>
							</TableBodyCell>
						</TableBodyRow>
						<TableBodyRow>
							<TableBodyCell tdClass="p-2 font-medium"
								>{$t('hardware-devices.table.last-seen')}</TableBodyCell
							>
							<TableBodyCell tdClass="p-2">
								{@const timestamp =
									data.device.last_seen &&
									(data.device.last_seen.includes('+')
										? data.device.last_seen
										: data.device.last_seen + '+0000')}
								{#if timestamp && new Date(timestamp) > new Date(new Date().getTime() - 30000)}
									<span class="text-green-500">{$t('hardware-devices.table.connected')}</span>
								{:else}
									<RenderTimeAgo {timestamp} />
								{/if}
							</TableBodyCell>
						</TableBodyRow>
					</TableBody>
				</Table>
			</Card>
		</Section>

		<!-- Hardware IDs section -->
		<Section class="col-span-3" title={$t('hardware-devices.hardware-ids')}>
			<Card class="w-full max-w-none">
				<Table shadow>
					<TableHead theadClass="text-xs normal-case">
						<TableHeadCell padding="p-2">{$t('hardware-devices.table.key')}</TableHeadCell>
						<TableHeadCell padding="p-2">{$t('hardware-devices.table.value')}</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each Object.entries(data.device.hardware_ids) as [hardwareIdKey, hardwareValue]}
							<TableBodyRow>
								<TableBodyCell tdClass="p-2 font-medium">
									{hardwareIdKey in hardwareKeyToDisplayName
										? hardwareKeyToDisplayName[hardwareIdKey]()
										: hardwareIdKey}
								</TableBodyCell>
								<TableBodyCell tdClass="p-2">
									{hardwareValue}
								</TableBodyCell>
							</TableBodyRow>
						{/each}
					</TableBody>
				</Table>
			</Card>
		</Section>

		<!-- Associated configuration section -->
		<Section class="col-span-3" title={$t('hardware-devices.associated-configuration')}>
			<Card class="w-full max-w-none">
				{#if data.device.deployment_info_id && data.deviceDeploymentInfo}
					{@const config = data.data?.globalState?.configs?.find(
						(c) => c.identifier === data.deviceDeploymentInfo?.deployed_config_id
					)}
					{@const deviceType = config && getDeviceType(config)}

					<Table shadow>
						<TableHead theadClass="text-xs normal-case">
							<TableHeadCell padding="p-2">{$t('hardware-devices.table.property')}</TableHeadCell>
							<TableHeadCell padding="p-2">{$t('hardware-devices.table.value')}</TableHeadCell>
						</TableHead>
						<TableBody>
							<TableBodyRow>
								<TableBodyCell tdClass="p-2 font-medium"
									>{$t('hardware-devices.table.configuration-name')}</TableBodyCell
								>
								<TableBodyCell tdClass="p-2">
									{#if config}
										<a
											href={`/configuration/configuration-details?${buildGlobalNavSearchParam(data.data?.globalState, $page.url.search, 'config', data.deviceDeploymentInfo.deployed_config_id)}`}
											class="underline flex items-center gap-2 w-fit"
										>
											<FileCode size={18} />
											{config.displayName}
										</a>
									{:else}
										<span>{$t('hardware-devices.unknown-configuration')}</span>
									{/if}
								</TableBodyCell>
							</TableBodyRow>
							<TableBodyRow>
								<TableBodyCell tdClass="p-2 font-medium"
									>{$t('hardware-devices.table.deployed-config-commit')}</TableBodyCell
								>
								<TableBodyCell tdClass="p-2">
									{#if data.deviceDeploymentInfo.deployed_config_commit}
										<span class="playwright-snapshot-unstable font-mono">
											{data.deviceDeploymentInfo.deployed_config_commit.slice(0, 8)}
										</span>
									{:else}
										<span>{$t('configuration-details.no-commit')}</span>
									{/if}
								</TableBodyCell>
							</TableBodyRow>
							<TableBodyRow>
								<TableBodyCell tdClass="p-2 font-medium"
									>{$t('hardware-devices.table.device-type')}</TableBodyCell
								>
								<TableBodyCell tdClass="p-2">
									{#if config}
										{deviceType && deviceType in deviceTypes ? deviceTypes[deviceType] : deviceType}
									{:else}
										<span>{$t('hardware-devices.table.unknown-device-type')}</span>
									{/if}
								</TableBodyCell>
							</TableBodyRow>
						</TableBody>
					</Table>
				{:else}
					<p class="p-4">{$t('hardware-devices.no-associated-config')}</p>
				{/if}
			</Card>
		</Section>

		<!-- VNC and Terminal sections if associated with deployment info -->
		{#if data.device.deployment_info_id && data.deviceDeploymentInfo && data.data?.globalState}
			{@const config = data.data.globalState.configs.find(
				(c) => c.identifier === data.deviceDeploymentInfo?.deployed_config_id
			)}

			{#if config && targetShouldShowVNC(config, data.data.globalState)}
				<Section class="col-span-4" title={$t('nav.device-vnc')}>
					<VncView
						globalState={data.data.globalState}
						{config}
						deploymentInfo={data.deviceDeploymentInfo}
					/>
				</Section>
			{/if}

			<Section class="col-span-4" title={$t('nav.terminal')}>
				<Card class="w-full max-w-none" padding="sm">
					<Terminal deploymentInfo={data.deviceDeploymentInfo} />
				</Card>
			</Section>
		{/if}
	</div>
{:else}
	<div class="bg-red-100 border border-red-500 text-red-700 px-4 py-3 rounded">
		<p>{$t('hardware-devices.device-not-found')}</p>
	</div>
{/if}
