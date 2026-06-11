<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Input, Label, Modal } from 'flowbite-svelte';
	import Pen from 'lucide-svelte/icons/pen';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { updateDeploymentInfo } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import { invalidate } from '$app/navigation';

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
		const response = await updateDeploymentInfo(fetch, deploymentInfo.id, {
			location: locationInput || null
		});
		if (response.ok) {
			modalOpen = false;
			await invalidate(`/api/deployment_info/${deploymentInfo.id}`);
		}
	}
</script>

<div class="ds-card flex flex-col w-full h-full">
	<div class="ds-card-head">
		<h2 class="ds-card-title">{$t('device-details.device-info')}</h2>
	</div>
	<div class="ds-card-pad">
		<div class="ds-kv">
			<!-- ID -->
			<div class="ds-kv-row">
				<span class="ds-kv-key">{$t('device-details.id')}</span>
				<span class="ds-kv-val mono">{deploymentInfo.id}</span>
			</div>

			<!-- Location -->
			<div class="ds-kv-row">
				<span class="ds-kv-key">{$t('device-details.location')}</span>
				<span class="ds-kv-val flex items-center gap-2">
					<span>{deploymentInfo.location ?? $t('device-details.no-location')}</span>
					<button
						onclick={openModal}
						class="shrink-0"
						style="color: var(--ds-text-mute)"
						title={$t('device-details.edit-location')}
					>
						<Pen size="0.875rem" />
					</button>
				</span>
			</div>

			<!-- Configuration -->
			<div class="ds-kv-row">
				<span class="ds-kv-key">{$t('device-details.configuration')}</span>
				<span class="ds-kv-val">
					{#if deploymentInfo.deployed_config_id}
						<IdentifierLink
							identifier={deploymentInfo.deployed_config_id}
							context="config"
							{globalState}
						/>
					{:else}
						<span style="color: var(--ds-text-mute)">-</span>
					{/if}
				</span>
			</div>

			<!-- Commit -->
			<div class="ds-kv-row">
				<span class="ds-kv-key">{$t('device-details.commit')}</span>
				<span class="ds-kv-val mono">
					{#if deploymentInfo.deployed_config_commit}
						{deploymentInfo.deployed_config_commit.slice(0, 8)}
					{:else}
						<span style="color: var(--ds-text-mute)">-</span>
					{/if}
				</span>
			</div>

			<!-- Hardware IDs -->
			{#if deploymentInfo.hardware_devices.length > 0}
				<div class="ds-kv-row">
					<span class="ds-kv-key">{$t('device-details.hardware-ids')}</span>
					<span class="ds-kv-val">
						{#each Object.entries(deploymentInfo.hardware_devices[0].hardware_ids) as [key, value]}
							<div class="ds-mono">{key}: {value}</div>
						{/each}
					</span>
				</div>
			{/if}

			<!-- First seen -->
			<div class="ds-kv-row">
				<span class="ds-kv-key">{$t('device-details.first-seen')}</span>
				<span class="ds-kv-val">
					{#if deploymentInfo.first_seen}
						<RenderTimeAgo timestamp={deploymentInfo.first_seen} />
					{:else}
						<span style="color: var(--ds-text-mute)">-</span>
					{/if}
				</span>
			</div>

			<!-- Last seen -->
			<div class="ds-kv-row">
				<span class="ds-kv-key">{$t('device-details.last-seen')}</span>
				<span class="ds-kv-val">
					{#if deploymentInfo.last_seen}
						<RenderTimeAgo timestamp={deploymentInfo.last_seen} />
					{:else}
						<span style="color: var(--ds-text-mute)">-</span>
					{/if}
				</span>
			</div>
		</div>

		<!-- Network Interfaces -->
		{#if deploymentInfo.network_interfaces?.length}
			<div class="mt-4 space-y-2">
				<p
					class="mb-1 text-xs font-semibold uppercase tracking-wide"
					style="color: var(--ds-text-mute)"
				>
					{$t('device-details.network-info')}
				</p>
				{#each deploymentInfo.network_interfaces as iface}
					<div class="ds-net-iface">
						<p class="ds-mono font-bold" style="color: var(--ds-text)">{iface.interface}</p>
						{#if iface.ipv4_addresses.length}
							<p class="ds-mono">IPv4: {iface.ipv4_addresses.join(', ')}</p>
						{/if}
						{#if iface.ipv6_addresses.length}
							<p class="ds-mono">IPv6: {iface.ipv6_addresses.join(', ')}</p>
						{/if}
						{#if iface.mac_address}
							<p class="ds-mono">MAC: {iface.mac_address}</p>
						{/if}
					</div>
				{/each}
			</div>
		{:else}
			<p class="mt-4 text-sm" style="color: var(--ds-text-dim)">
				{$t('device-details.no-network-info')}
			</p>
		{/if}
	</div>
</div>

<Modal bind:open={modalOpen} title={$t('device-details.edit-location')}>
	<Label class="mb-1">{$t('device-details.location')}</Label>
	<Input bind:value={locationInput} placeholder={$t('device-details.location-placeholder')} />
	<div class="mt-4 flex justify-end gap-2">
		<button class="ds-btn" onclick={() => (modalOpen = false)}>{$t('common.cancel')}</button>
		<button class="ds-btn ds-btn-primary" onclick={save}>{$t('device-details.save')}</button>
	</div>
</Modal>
