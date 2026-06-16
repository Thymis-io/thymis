<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FleetAvailability } from '$lib/fleet';

	interface Props {
		availability: FleetAvailability;
	}
	let { availability }: Props = $props();

	const rows = $derived(availability.devices);

	function uptimePct(states: boolean[]): number {
		if (!states.length) return 0;
		return Math.round((states.filter(Boolean).length / states.length) * 100);
	}
</script>

<div class="ds-card-pad">
	{#if !rows.length}
		<p class="text-sm" style="color: var(--ds-text-dim)">
			{$t('overview.availability.no-data')}
		</p>
	{:else}
		<div class="space-y-2">
			{#each rows as row (row.deployment_info_id)}
				<a href={`/devices/${row.deployment_info_id}`} class="block">
					<div class="mb-1 flex items-baseline justify-between text-xs">
						<span class="truncate" style="color: var(--ds-text)">
							{row.name ?? row.deployment_info_id.slice(0, 8)}
						</span>
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
				</a>
			{/each}
		</div>
	{/if}
</div>
