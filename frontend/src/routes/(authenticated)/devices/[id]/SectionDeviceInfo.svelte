<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Card, Input, Label, Modal } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { updateLocation } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';

	interface Props {
		deploymentInfo: DeploymentInfo;
		globalState: GlobalState;
	}
	let { deploymentInfo = $bindable(), globalState }: Props = $props();

	let modalOpen = $state(false);
	let locationInput = $state('');

	function openModal() {
		locationInput = deploymentInfo.location ?? '';
		modalOpen = true;
	}

	async function save() {
		const response = await updateLocation(fetch, deploymentInfo.id, locationInput || null);
		if (response.ok) {
			deploymentInfo = { ...deploymentInfo, location: locationInput || null };
			modalOpen = false;
		}
	}
</script>

<Card>
	<h2 class="mb-4 text-xl font-semibold">{$t('device-details.device-info')}</h2>
	<div class="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-2 text-sm">
		<!-- Location -->
		<span class="font-medium text-gray-500">{$t('device-details.location')}</span>
		<div class="flex items-center gap-2">
			<span>{deploymentInfo.location ?? $t('device-details.no-location')}</span>
			<button
				onclick={openModal}
				class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
				title={$t('device-details.edit-location')}
			>
				<Pen size="0.875rem" />
			</button>
		</div>

		<!-- Configuration -->
		<span class="font-medium text-gray-500">{$t('device-details.configuration')}</span>
		<div>
			{#if deploymentInfo.deployed_config_id}
				<IdentifierLink
					identifier={deploymentInfo.deployed_config_id}
					context="config"
					{globalState}
				/>
			{:else}
				<span class="text-gray-400">—</span>
			{/if}
		</div>

		<!-- Commit -->
		<span class="font-medium text-gray-500">{$t('device-details.commit')}</span>
		<span>
			{#if deploymentInfo.deployed_config_commit}
				<span class="font-mono">{deploymentInfo.deployed_config_commit.slice(0, 8)}</span>
			{:else}
				<span class="text-gray-400">—</span>
			{/if}
		</span>

		<!-- Hardware IDs -->
		{#if deploymentInfo.hardware_devices.length > 0}
			<span class="font-medium text-gray-500">{$t('device-details.hardware-ids')}</span>
			<div>
				{#each Object.entries(deploymentInfo.hardware_devices[0].hardware_ids) as [key, value]}
					<div class="font-mono text-xs">{key}: {value}</div>
				{/each}
			</div>
		{/if}

		<!-- First seen -->
		<span class="font-medium text-gray-500">{$t('device-details.first-seen')}</span>
		<span>
			{#if deploymentInfo.first_seen}
				<RenderTimeAgo timestamp={deploymentInfo.first_seen} />
			{:else}
				<span class="text-gray-400">—</span>
			{/if}
		</span>

		<!-- Last seen -->
		<span class="font-medium text-gray-500">{$t('device-details.last-seen')}</span>
		<span>
			{#if deploymentInfo.last_seen}
				<RenderTimeAgo timestamp={deploymentInfo.last_seen} />
			{:else}
				<span class="text-gray-400">—</span>
			{/if}
		</span>
	</div>

	<!-- Network Interfaces -->
	{#if deploymentInfo.network_interfaces?.length}
		<div class="mt-4 space-y-2">
			<p class="text-sm font-medium text-gray-500">{$t('device-details.network-info')}</p>
			{#each deploymentInfo.network_interfaces as iface}
				<div class="rounded border border-gray-200 p-2 dark:border-gray-600">
					<p class="font-mono font-bold text-sm">{iface.interface}</p>
					{#if iface.ipv4_addresses.length}
						<p class="font-mono text-xs text-gray-600 dark:text-gray-400">
							IPv4: {iface.ipv4_addresses.join(', ')}
						</p>
					{/if}
					{#if iface.ipv6_addresses.length}
						<p class="font-mono text-xs text-gray-600 dark:text-gray-400">
							IPv6: {iface.ipv6_addresses.join(', ')}
						</p>
					{/if}
					{#if iface.mac_address}
						<p class="font-mono text-xs text-gray-600 dark:text-gray-400">
							MAC: {iface.mac_address}
						</p>
					{/if}
				</div>
			{/each}
		</div>
	{:else}
		<p class="mt-4 text-sm text-gray-500">{$t('device-details.no-network-info')}</p>
	{/if}
</Card>

<Modal bind:open={modalOpen} title={$t('device-details.edit-location')}>
	<Label class="mb-1">{$t('device-details.location')}</Label>
	<Input bind:value={locationInput} placeholder={$t('device-details.location-placeholder')} />
	<div class="mt-4 flex gap-2">
		<Button onclick={save}>{$t('device-details.save')}</Button>
		<Button color="light" onclick={() => (modalOpen = false)}>{$t('common.cancel')}</Button>
	</div>
</Modal>
