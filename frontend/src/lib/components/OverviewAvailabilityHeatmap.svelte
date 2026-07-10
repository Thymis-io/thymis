<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FleetAvailability } from '$lib/fleet';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		globalState: GlobalState;
		availability: FleetAvailability;
	}
	let { globalState, availability }: Props = $props();

	const rows = $derived(availability.devices);

	function uptimePct(states: boolean[]): number {
		if (!states.length) return 0;
		return Math.round((states.filter(Boolean).length / states.length) * 100);
	}
</script>

<div class="ds-card-pad ds-card-scroll">
	{#if !rows.length}
		<p class="text-sm" style="color: var(--ds-text-dim)">
			{$t('overview.availability.no-data')}
		</p>
	{:else}
		<div class="space-y-2">
			{#each rows as row (row.deployment_info_id)}
				{@const deploymentInfo = globalState.deploymentInfos.find(
					(di) => di.id === row.deployment_info_id
				)}
				<div class="block">
					<div class="mb-1 flex items-center justify-between text-xs">
						<div class="flex items-center gap-1.5">
							<span
								class="h-2 w-2 flex-shrink-0 rounded-full {deploymentInfo?.connected
									? 'bg-emerald-500'
									: 'bg-gray-400'}"
								title={deploymentInfo?.connected ? $t('overview.online') : $t('overview.offline')}
							></span>
							<IdentifierLink {globalState} identifier={row.deployment_info_id} context="device" />
						</div>
						<span style="color: var(--ds-text-dim)">{uptimePct(row.states)}%</span>
					</div>
					<div class="flex gap-px overflow-hidden rounded">
						{#each row.states as online}
							<div
								class="h-3 flex-1"
								style="background: {online
									? 'var(--ds-online, #10b981)'
									: 'var(--ds-offline, #ef4444)'}"
								title={online ? $t('overview.online') : $t('overview.offline')}
							></div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
