<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { DeviceMetricsEntry } from '#lib/deploymentInfo.js';
	import { Line } from 'svelte-chartjs';
	import {
		Chart as ChartJS,
		CategoryScale,
		LinearScale,
		PointElement,
		LineElement,
		Title,
		Tooltip,
		Legend,
		type TooltipItem
	} from 'chart.js';

	ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

	interface Props {
		metrics: DeviceMetricsEntry[];
		timewindow: '1h' | '24h' | '7d';
	}
	let { metrics, timewindow }: Props = $props();

	const latest = $derived(metrics.length ? metrics[metrics.length - 1] : null);

	const TICK_STEP_MS: Record<string, number> = {
		'1h': 10 * 60 * 1000,
		'24h': 2 * 60 * 60 * 1000,
		'7d': 24 * 60 * 60 * 1000
	};

	function formatTime(ms: number): string {
		return new Date(ms).toLocaleString(undefined, {
			month: timewindow === '7d' ? '2-digit' : undefined,
			day: timewindow === '7d' ? '2-digit' : undefined,
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	const series = [
		{ key: 'cpu_percent' as const, label: 'CPU', color: 'rgb(255, 99, 132)' },
		{ key: 'ram_percent' as const, label: 'RAM', color: 'rgb(54, 162, 235)' },
		{ key: 'disk_percent' as const, label: 'Disk', color: 'rgb(255, 193, 7)' }
	];

	const data = $derived({
		datasets: series.map((s) => ({
			label: s.label,
			data: metrics.map((m) => ({ x: new Date(m.timestamp).getTime(), y: m[s.key] })),
			borderColor: s.color,
			backgroundColor: `color-mix(in srgb, ${s.color} 10%, transparent)`,
			tension: 0.3,
			pointRadius: 2
		}))
	});

	const chartOptions = $derived({
		responsive: true,
		maintainAspectRatio: false,
		animation: false as const,
		plugins: {
			legend: { display: true },
			tooltip: {
				callbacks: {
					title: (items: TooltipItem<'line'>[]) => formatTime(Number(items[0].parsed.x)),
					label: (item: TooltipItem<'line'>) =>
						`${item.dataset.label}: ${(item.parsed.y ?? 0).toFixed(1)}%`
				}
			}
		},
		scales: {
			x: {
				type: 'linear' as const,
				ticks: {
					stepSize: TICK_STEP_MS[timewindow],
					callback: (value: string | number) => formatTime(Number(value))
				}
			},
			y: { min: 0, max: 100 }
		}
	});
</script>

{#if !metrics.length}
	<p class="text-sm" style="color: var(--ds-text-dim)">{$t('device-details.no-metrics')}</p>
{:else}
	<div class="mb-4 grid grid-cols-3 gap-3">
		{#each series as item (item.key)}
			<div class="ds-stat">
				<div class="ds-stat-label flex items-center gap-1.5">
					<span
						class="inline-block h-2 w-2 flex-shrink-0 rounded-full"
						style="background: {item.color}"
					></span>
					{item.label}
				</div>
				<div class="ds-stat-value">{(latest?.[item.key] ?? 0).toFixed(1)}%</div>
			</div>
		{/each}
	</div>
	<div class="relative h-72 w-full">
		<Line {data} options={chartOptions} />
	</div>
{/if}
