<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FleetDeviceMetric } from '$lib/fleet';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import { isOnline } from '$lib/deploymentInfo';

	interface Props {
		globalState: GlobalState;
		devices: FleetDeviceMetric[];
		limit?: number;
	}

	let { globalState, devices, limit = 5 }: Props = $props();

	type Metric = 'cpu' | 'ram' | 'disk';
	const columns: { metric: Metric; field: keyof FleetDeviceMetric; color: string }[] = [
		{ metric: 'cpu', field: 'cpu_percent', color: '#ef4444' },
		{ metric: 'ram', field: 'ram_percent', color: '#3b82f6' },
		{ metric: 'disk', field: 'disk_percent', color: '#f59e0b' }
	];

	function top(field: keyof FleetDeviceMetric) {
		return [...devices].sort((a, b) => (b[field] as number) - (a[field] as number)).slice(0, limit);
	}
</script>

<div class="ds-card-pad">
	{#if !devices.length}
		<p class="text-sm" style="color: var(--ds-text-dim)">{$t('overview.fleet.no-load-data')}</p>
	{:else}
		<div class="grid grid-cols-1 gap-6 md:grid-cols-3">
			{#each columns as col (col.metric)}
				<div>
					<h4 class="mb-2 text-xs font-semibold uppercase" style="color: var(--ds-text-dim)">
						{$t(`overview.fleet.${col.metric}`)}
					</h4>
					<div class="space-y-2">
						{#each top(col.field) as d (d.deployment_info_id)}
							{@const pct = d[col.field] as number}
							{@const deploymentInfo = globalState.deploymentInfos.find(
								(di) => di.id === d.deployment_info_id
							)}
							{@const online = deploymentInfo && isOnline(deploymentInfo?.last_seen)}
							<div class="block">
								<div class="mb-1 flex items-baseline justify-between text-sm">
									<div class="flex items-center gap-2">
										<span
											class={[
												'h-2 w-2 flex-shrink-0 rounded-full inline-block',
												online ? 'bg-emerald-500' : 'bg-gray-400'
											].join(' ')}
										></span>
										<IdentifierLink
											{globalState}
											identifier={d.deployment_info_id}
											context="device"
										/>
									</div>
									<span style="color: var(--ds-text-dim)">{pct.toFixed(0)}%</span>
								</div>
								<div
									class="h-2 w-full overflow-hidden rounded-full"
									style="background: var(--ds-border)"
								>
									<div
										class="h-full rounded-full"
										style="width: {Math.min(100, pct)}%; background: {col.color}"
									></div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
