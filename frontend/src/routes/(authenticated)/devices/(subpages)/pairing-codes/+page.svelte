<script lang="ts">
	import { t } from 'svelte-i18n';
	import { invalidate } from '$app/navigation';
	import { Modal } from 'flowbite-svelte';
	import type { PageData } from './$types';
	import DataTable from '#lib/components/layout/DataTable.svelte';
	import RowActions from '#lib/components/layout/RowActions.svelte';
	import RowMenu from '#lib/components/layout/RowMenu.svelte';
	import RenderTimeAgo from '#lib/components/RenderTimeAgo.svelte';
	import PairingCodeDisplay from '#lib/components/PairingCodeDisplay.svelte';
	import { revokePairingCode, type PairingCode } from '#lib/pairingCodes.js';
	import Info from 'lucide-svelte/icons/info';
	import Ban from 'lucide-svelte/icons/ban';
	import Terminal from 'lucide-svelte/icons/terminal';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let shownCode = $state<PairingCode | undefined>();

	const revoke = async (id: string) => {
		await revokePairingCode(id);
		await invalidate('/api/pairing-codes');
	};

	type Status = { label: string; pill: 'online' | 'offline' | 'danger' };

	const status = (pairingCode: PairingCode): Status => {
		if (pairingCode.redeemed_at)
			return { label: $t('pairing-codes.status.redeemed'), pill: 'online' };
		if (pairingCode.revoked) return { label: $t('pairing-codes.status.revoked'), pill: 'danger' };
		return { label: $t('pairing-codes.status.expired'), pill: 'offline' };
	};

	const formatDate = (timestamp: string) => new Date(timestamp).toLocaleString();
</script>

<div class="ds-card ds-card-pad mb-4 flex items-start gap-3">
	<Info size={18} class="mt-0.5 shrink-0" style="color: var(--ds-accent)" />
	<div class="flex flex-col gap-1 text-base">
		<span class="font-medium">{$t('pairing-codes.info-title')}</span>
		<span>{$t('pairing-codes.external-only')}</span>
	</div>
</div>

<h2 class="ds-section-title mb-2">{$t('pairing-codes.active')}</h2>
<DataTable
	class="mb-6"
	columns={[
		{ label: $t('pairing-codes.table.code') },
		{ label: $t('pairing-codes.table.created') },
		{ label: $t('pairing-codes.table.expires') },
		{}
	]}
	rows={data.pairingCodes.active}
	rowKey={(pc) => pc.id}
	empty={$t('pairing-codes.no-active')}
>
	{#snippet row(pairingCode)}
		<td class="playwright-snapshot-unstable" style="font-family: var(--ds-mono)">
			{pairingCode.code}
		</td>
		<td><RenderTimeAgo timestamp={pairingCode.created_at} /></td>
		<td class="playwright-snapshot-unstable">{formatDate(pairingCode.expires_at)}</td>
		<td>
			<RowActions>
				<RowMenu
					label={$t('pairing-codes.actions')}
					menuWidth={220}
					items={[
						{
							label: $t('pairing-codes.show-instructions'),
							icon: Terminal,
							onclick: () => (shownCode = pairingCode)
						},
						{
							label: $t('pairing-codes.revoke'),
							icon: Ban,
							variant: 'danger',
							onclick: () => revoke(pairingCode.id)
						}
					]}
				/>
			</RowActions>
		</td>
	{/snippet}
</DataTable>

<h2 class="ds-section-title mb-1">{$t('pairing-codes.recent')}</h2>
<p class="mb-2 text-sm">{$t('pairing-codes.recent-hint')}</p>
<DataTable
	columns={[
		{ label: $t('pairing-codes.table.code') },
		{ label: $t('pairing-codes.table.status') },
		{ label: $t('pairing-codes.table.created') },
		{ label: $t('pairing-codes.table.redeemed') }
	]}
	rows={data.pairingCodes.recent}
	rowKey={(pc) => pc.id}
	empty={$t('pairing-codes.no-recent')}
>
	{#snippet row(pairingCode)}
		{@const s = status(pairingCode)}
		<td class="playwright-snapshot-unstable" style="font-family: var(--ds-mono)">
			{pairingCode.code}
		</td>
		<td><span class="ds-status-pill {s.pill}">{s.label}</span></td>
		<td><RenderTimeAgo timestamp={pairingCode.created_at} /></td>
		<td>
			{#if pairingCode.redeemed_at}
				<RenderTimeAgo timestamp={pairingCode.redeemed_at} />
			{:else}
				<span style="color: var(--ds-text-mute)">-</span>
			{/if}
		</td>
	{/snippet}
</DataTable>

<Modal
	open={!!shownCode}
	title={$t('pairing-codes.instructions-title')}
	size="lg"
	outsideclose
	on:close={() => (shownCode = undefined)}
>
	{#if shownCode}
		<PairingCodeDisplay
			pairingCode={shownCode}
			controllerUrl={data.controllerInfo.agent_access_url}
		/>
	{/if}
</Modal>
