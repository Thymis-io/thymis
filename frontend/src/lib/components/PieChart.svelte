<script lang="ts">
	import HeadTag from './HeadTag.svelte';

	export type PieSlice = {
		label: string;
		value: number;
		color: string;
		isHead?: boolean;
	};

	interface Props {
		slices: PieSlice[];
		size?: number;
		title?: string;
	}

	let { slices, size = 200, title = '' }: Props = $props();

	const COLORS = [
		'#3b82f6', // blue-500
		'#10b981', // emerald-500
		'#f59e0b', // amber-500
		'#ef4444', // red-500
		'#8b5cf6', // violet-500
		'#ec4899', // pink-500
		'#14b8a6', // teal-500
		'#f97316', // orange-500
		'#6366f1', // indigo-500
		'#84cc16' // lime-500
	];

	let cx = $derived(size / 2);
	let cy = $derived(size / 2);
	let r = $derived(size / 2 - 10);

	type ArcPath = {
		path: string;
		label: string;
		color: string;
		value: number;
		midX: number;
		midY: number;
		percentage: number;
	};

	let total = $derived(slices.reduce((sum, s) => sum + s.value, 0));

	let arcs = $derived((): ArcPath[] => {
		if (total === 0) return [];
		const paths: ArcPath[] = [];
		let startAngle = -Math.PI / 2;
		for (let i = 0; i < slices.length; i++) {
			const slice = slices[i];
			const fraction = slice.value / total;
			const sweepAngle = fraction * 2 * Math.PI;
			const endAngle = startAngle + sweepAngle;

			const x1 = cx + r * Math.cos(startAngle);
			const y1 = cy + r * Math.sin(startAngle);
			const x2 = cx + r * Math.cos(endAngle);
			const y2 = cy + r * Math.sin(endAngle);
			const largeArc = sweepAngle > Math.PI ? 1 : 0;

			const midAngle = startAngle + sweepAngle / 2;
			const midX = cx + r * 0.65 * Math.cos(midAngle);
			const midY = cy + r * 0.65 * Math.sin(midAngle);

			let path: string;
			if (fraction >= 1) {
				// full circle — draw as two half-arcs
				const mx = cx + r * Math.cos(startAngle + Math.PI);
				const my = cy + r * Math.sin(startAngle + Math.PI);
				path = `M ${x1} ${y1} A ${r} ${r} 0 1 1 ${mx} ${my} A ${r} ${r} 0 1 1 ${x1} ${y1} Z`;
			} else {
				path = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`;
			}

			paths.push({
				path,
				label: slice.label,
				color: slice.color || COLORS[i % COLORS.length],
				value: slice.value,
				midX,
				midY,
				percentage: Math.round(fraction * 100)
			});
			startAngle = endAngle;
		}
		return paths;
	});
</script>

<div class="flex flex-col items-center gap-3">
	{#if title}
		<h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200 text-center">{title}</h3>
	{/if}

	{#if total === 0}
		<div
			class="flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 text-xs"
			style="width:{size}px;height:{size}px"
		>
			No data
		</div>
	{:else}
		<svg width={size} height={size} viewBox="0 0 {size} {size}">
			{#each arcs() as arc (arc.label)}
				<path d={arc.path} fill={arc.color} stroke="white" stroke-width="1.5">
					<title>{arc.label}: {arc.value} ({arc.percentage}%)</title>
				</path>
				{#if arc.percentage >= 8}
					<text
						x={arc.midX}
						y={arc.midY}
						text-anchor="middle"
						dominant-baseline="middle"
						font-size="10"
						fill="white"
						font-weight="600"
						pointer-events="none"
					>
						{arc.percentage}%
					</text>
				{/if}
			{/each}
		</svg>
	{/if}

	<!-- Legend -->
	<ul class="flex flex-row flex-wrap justify-center gap-x-6 gap-y-2 w-full">
		{#each slices as slice, i (slice.label)}
			<li class="flex items-center gap-1 text-xs text-gray-700 dark:text-gray-300">
				<span
					class="inline-block rounded-sm flex-shrink-0"
					style="width:12px;height:12px;background:{slice.color || COLORS[i % COLORS.length]}"
				></span>
				<span class="truncate flex-1">{slice.label}</span>
				{#if slice.isHead}
					<HeadTag />
				{/if}
				<span class="font-mono font-semibold flex-shrink-0">{slice.value}</span>
			</li>
		{/each}
	</ul>
</div>
