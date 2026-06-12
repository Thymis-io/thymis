<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FleetDeviceMetric } from '$lib/fleet';

	interface Props {
		devices: FleetDeviceMetric[];
		limit?: number;
	}
	let { devices, limit = 5 }: Props = $props();

	type Metric = 'cpu' | 'ram' | 'disk';
	let metric: Metric = $state('cpu');

	const fieldMap: Record<Metric, keyof FleetDeviceMetric> = {
		cpu: 'cpu_percent',
		ram: 'ram_percent',
		disk: 'disk_percent'
	};

	const barColor: Record<Metric, string> = {
		cpu: '#ef4444',
		ram: '#3b82f6',
		disk: '#f59e0b'
	};

	const top = $derived(
		[...devices]
			.sort((a, b) => (b[fieldMap[metric]] as number) - (a[fieldMap[metric]] as number))
			.slice(0, limit)
	);
</script>

<div class="ds-card-pad">
	<div class="mb-3 flex gap-1">
		{#each ['cpu', 'ram', 'disk'] as const as m}
			<button
				class="ds-btn ds-btn-sm {metric === m ? 'ds-btn-primary' : ''}"
				onclick={() => (metric = m)}
			>
				{$t(`overview.fleet.${m}`)}
			</button>
		{/each}
	</div>

	{#if !top.length}
		<p class="text-sm" style="color: var(--ds-text-dim)">{$t('overview.fleet.no-load-data')}</p>
	{:else}
		<div class="space-y-2">
			{#each top as d (d.deployment_info_id)}
				{@const pct = d[fieldMap[metric]] as number}
				<a href={`/devices/${d.deployment_info_id}`} class="block">
					<div class="mb-1 flex items-baseline justify-between text-sm">
						<span class="truncate" style="color: var(--ds-text)"
							>{d.name ?? d.deployment_info_id.slice(0, 8)}</span
						>
						<span style="color: var(--ds-text-dim)">{pct.toFixed(0)}%</span>
					</div>
					<div class="h-2 w-full overflow-hidden rounded-full" style="background: var(--ds-border)">
						<div
							class="h-full rounded-full"
							style="width: {Math.min(100, pct)}%; background: {barColor[metric]}"
						></div>
					</div>
				</a>
			{/each}
		</div>
	{/if}
</div>
