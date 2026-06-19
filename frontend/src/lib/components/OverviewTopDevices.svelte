<script lang="ts">
	import { t } from 'svelte-i18n';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import type { FleetDeviceMetric } from '$lib/fleet';

	interface Props {
		devices: FleetDeviceMetric[];
		limit?: number;
	}
	let { devices, limit = 5 }: Props = $props();

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
							<a href={`/devices/${d.deployment_info_id}`} class="device-link block">
								<div class="mb-1 flex items-baseline justify-between text-sm">
									<span class="flex min-w-0 items-center gap-1" style="color: var(--ds-text)">
										<HardDrive size={14} class="shrink-0" />
										<span class="device-name truncate">
											{d.name ?? d.deployment_info_id.slice(0, 8)}
										</span>
									</span>
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
							</a>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	/* Underline the device name on hover, matching the other device links. */
	.device-link:hover .device-name {
		text-decoration: underline;
	}
</style>
