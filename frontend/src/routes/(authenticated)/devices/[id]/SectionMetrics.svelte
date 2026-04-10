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
		Legend
	} from 'chart.js';

	ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

	interface Props {
		metrics: DeviceMetricsEntry[];
		timewindow: '1h' | '24h' | '7d';
	}
	let { metrics, timewindow }: Props = $props();

	const latest = $derived(metrics.length ? metrics[metrics.length - 1] : null);

	function parseTimestamp(ts: string): Date {
		// Backend returns "YYYY-MM-DD HH", "YYYY-MM-DD HH:MM" — not valid ISO
		const normalized =
			ts.replace(' ', 'T') + (ts.length <= 13 ? ':00:00' : ts.length <= 16 ? ':00' : '');
		return new Date(normalized);
	}

	function formatLabel(ts: string): string {
		const d = parseTimestamp(ts);
		if (timewindow === '7d') {
			return (
				d.toLocaleDateString(undefined, { month: '2-digit', day: '2-digit' }) +
				' ' +
				d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
			);
		}
		return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
	}

	function chartData(key: 'cpu_percent' | 'ram_percent' | 'disk_percent', color: string) {
		return {
			labels: metrics.map((m) => formatLabel(m.timestamp)),
			datasets: [
				{
					label: { cpu_percent: 'CPU', ram_percent: 'RAM', disk_percent: 'Disk' }[key],
					data: metrics.map((m) => m[key]),
					borderColor: color,
					backgroundColor: color.replace('rgb(', 'rgba(').replace(')', ', 0.1)'),
					tension: 0.4,
					pointRadius: 0
				}
			]
		};
	}

	const chartOptions = {
		responsive: true,
		maintainAspectRatio: false,
		scales: { y: { min: 0, max: 100 } }
	};

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
					<Line data={chartData(item.key, item.color)} options={chartOptions} />
				</div>
			</div>
		{/each}
	</div>
{/if}
