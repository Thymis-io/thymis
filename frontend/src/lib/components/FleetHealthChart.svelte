<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { FleetMetricPoint } from '$lib/fleet';
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
		metrics: FleetMetricPoint[];
		timewindow: '1h' | '24h' | '7d';
	}
	let { metrics, timewindow }: Props = $props();

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
		{ key: 'cpu_avg' as const, label: 'CPU', color: 'rgb(255, 99, 132)' },
		{ key: 'ram_avg' as const, label: 'RAM', color: 'rgb(54, 162, 235)' },
		{ key: 'disk_avg' as const, label: 'Disk', color: 'rgb(255, 193, 7)' }
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
	<p class="text-sm" style="color: var(--ds-text-dim)">{$t('overview.fleet.no-metrics')}</p>
{:else}
	<div class="relative h-64 w-full">
		<Line {data} options={chartOptions} />
	</div>
{/if}
