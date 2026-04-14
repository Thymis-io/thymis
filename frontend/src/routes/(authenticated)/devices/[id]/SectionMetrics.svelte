<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Progressbar } from 'flowbite-svelte';
	import type { DeviceMetricsEntry } from '$lib/deploymentInfo';
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

	function chartData(
		key: 'cpu_percent' | 'ram_percent' | 'disk_percent',
		label: string,
		color: string
	) {
		return {
			datasets: [
				{
					label,
					data: metrics.map((m) => ({
						x: new Date(m.timestamp).getTime(),
						y: m[key].toFixed(2)
					})),
					borderColor: color,
					backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`,
					tension: 0.3,
					pointRadius: 3
				}
			]
		};
	}

	const chartOptions = $derived({
		responsive: true,
		maintainAspectRatio: false,
		plugins: {
			tooltip: {
				callbacks: {
					title: (items: TooltipItem<'line'>[]) => formatTime(Number(items[0].parsed.x)),
					label: (item: TooltipItem<'line'>) => `${item.parsed.y}%`
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

	const metricItems = [
		{ key: 'cpu_percent' as const, label: 'CPU', color: 'rgb(255, 99, 132)' },
		{ key: 'ram_percent' as const, label: 'RAM', color: 'rgb(54, 162, 235)' },
		{ key: 'disk_percent' as const, label: 'Disk', color: 'rgb(255, 193, 7)' }
	];
</script>

{#if !metrics.length}
	<p class="text-gray-500">{$t('device-details.no-metrics')}</p>
{:else}
	<div class="grid w-full grid-cols-1 gap-6 lg:grid-cols-3">
		{#each metricItems as item}
			<div class="rounded border border-gray-200 p-4">
				<div class="mb-3 flex items-center justify-between">
					<h4 class="text-sm font-semibold">{item.label}</h4>
					<span class="text-sm font-bold">{(latest?.[item.key] ?? 0).toFixed(1)}%</span>
				</div>
				<Progressbar progress={latest?.[item.key] ?? 0} class="mb-4" />
				<div class="relative h-56">
					<Line data={chartData(item.key, item.label, item.color)} options={chartOptions} />
				</div>
			</div>
		{/each}
	</div>
{/if}
