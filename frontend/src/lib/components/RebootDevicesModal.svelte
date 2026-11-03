<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Modal } from 'flowbite-svelte';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import IdentifierLink from '#lib/IdentifierLink.svelte';
	import { fetchWithNotify } from '#lib/fetchWithNotify.js';
	import type { DeploymentInfo } from '#lib/deploymentInfo.js';
	import type { GlobalState } from '#lib/state.svelte.js';

	interface Props {
		open?: boolean;
		devices: DeploymentInfo[];
		globalState: GlobalState;
		/** Called after the reboot request was accepted. */
		onRebooted?: () => void;
	}

	let { open = $bindable(false), devices, globalState, onRebooted }: Props = $props();

	let onlineCount = $derived(devices.filter((d) => d.connected).length);
	let submitting = $state(false);

	async function reboot() {
		submitting = true;
		try {
			const params = new URLSearchParams();
			for (const d of devices) params.append('deployment_info_id', d.id);
			const response = await fetchWithNotify(`/api/action/reboot-devices?${params}`, {
				method: 'POST'
			});
			if (response.ok) {
				open = false;
				onRebooted?.();
			}
		} finally {
			submitting = false;
		}
	}
</script>

<Modal bind:open title={$t('reboot.title')}>
	<p class="text-sm" style="color: var(--ds-text-dim)">{$t('reboot.description')}</p>
	<ul class="mt-3 flex max-h-[50vh] flex-col gap-2 overflow-y-auto">
		{#each devices as device (device.id)}
			<li class="flex flex-col gap-1 rounded-lg border border-[var(--ds-border)] p-2">
				<div class="flex items-center justify-between gap-2">
					<IdentifierLink
						identifier={device.id}
						context="device"
						deploymentInfo={device}
						{globalState}
					/>
					{#if !device.connected}
						<span class="ds-tag" style="color: var(--ds-text-mute)">
							{$t('reboot.will-be-skipped')}
						</span>
					{/if}
				</div>
				{#if device.reboot_required_reason}
					<span class="text-xs" style="color: var(--ds-warning)">
						{device.reboot_required_reason}
					</span>
				{/if}
			</li>
		{/each}
	</ul>
	{#if onlineCount === 0}
		<p class="mt-3 text-sm" style="color: var(--ds-text-mute)">{$t('reboot.no-online-targets')}</p>
	{/if}
	<div class="mt-4 flex justify-end gap-2">
		<button class="ds-btn" onclick={() => (open = false)}>{$t('common.cancel')}</button>
		<button
			class="ds-btn ds-btn-primary disabled:cursor-not-allowed disabled:opacity-50"
			onclick={reboot}
			disabled={onlineCount === 0 || submitting}
		>
			<RotateCcw size={'1rem'} class="min-w-4" />
			{$t('reboot.confirm', { values: { count: onlineCount } })}
		</button>
	</div>
</Modal>
