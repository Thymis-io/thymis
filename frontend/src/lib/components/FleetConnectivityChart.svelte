<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { ConnectivityPoint } from '$lib/fleet';
	import { Line } from 'svelte-chartjs';
	import {
		Chart as ChartJS,
		CategoryScale,
		LinearScale,
		PointElement,
		LineElement,
		Filler,
		Title,
		Tooltip,
		Legend,
		type TooltipItem
	} from 'chart.js';

	ChartJS.register(
		CategoryScale,
		LinearScale,
		PointElement,
		LineElement,
		Filler,
		Title,
		Tooltip,
		Legend
	);

	interface Props {
		points: ConnectivityPoint[];
		timewindow: '1h' | '24h' | '7d';
	}
	let { points, timewindow }: Props = $props();

	function formatTime(ms: number): string {
		return new Date(ms).toLocaleString(undefined, {
			month: timewindow === '7d' ? '2-digit' : undefined,
			day: timewindow === '7d' ? '2-digit' : undefined,
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	const maxCount = $derived(points.reduce((m, p) => Math.max(m, p.connected_count), 0));

	const data = $derived({
		datasets: [
			{
				label: $t('overview.fleet.connected'),
				data: points.map((p) => ({ x: new Date(p.timestamp).getTime(), y: p.connected_count })),
				borderColor: '#10b981',
				backgroundColor: 'color-mix(in srgb, #10b981 15%, transparent)',
				fill: true,
				tension: 0.3,
				pointRadius: 0
			}
		]
	});

	const chartOptions = $derived({
		responsive: true,
		maintainAspectRatio: false,
		animation: false as const,
		plugins: {
			legend: { display: false },
			tooltip: {
				callbacks: {
					title: (items: TooltipItem<'line'>[]) => formatTime(Number(items[0].parsed.x)),
					label: (item: TooltipItem<'line'>) => `${item.parsed.y}`
				}
			}
		},
		scales: {
			x: {
				type: 'linear' as const,
				ticks: { callback: (value: string | number) => formatTime(Number(value)) }
			},
			y: { min: 0, suggestedMax: Math.max(1, maxCount), ticks: { precision: 0 } }
		}
	});
</script>

{#if !points.length}
	<p class="text-sm" style="color: var(--ds-text-dim)">{$t('overview.fleet.no-metrics')}</p>
{:else}
	<div class="relative h-64 w-full">
		<Line {data} options={chartOptions} />
	</div>
{/if}
