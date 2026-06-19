<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type DeploymentInfo } from '$lib/deploymentInfo';
	import { getDeviceType, getDeviceTypesMap } from '$lib/config/configUtils';
	import type { GlobalState } from '$lib/state.svelte';
	import type { Module } from '$lib/state';

	interface Props {
		deploymentInfos: DeploymentInfo[];
		globalState: GlobalState;
		availableModules: Module[];
	}
	let { deploymentInfos, globalState, availableModules }: Props = $props();

	const active = $derived(deploymentInfos.filter((di) => !di.archived));
	const deviceTypesMap = $derived(getDeviceTypesMap(availableModules));
	const configByIdentifier = $derived(
		new Map(globalState.configs.map((cfg) => [cfg.identifier, cfg]))
	);

	// Higher-contrast categorical palette (distinct hues, consistent saturation).
	const PALETTE = ['#2563eb', '#16a34a', '#9333ea', '#db2777', '#0d9488', '#ea580c', '#ca8a04'];

	type TypeBar = { label: string; value: number; color: string };

	const bars = $derived.by<TypeBar[]>(() => {
		const counts = new Map<string, number>();
		for (const di of active) {
			const cfg = di.deployed_config_id ? configByIdentifier.get(di.deployed_config_id) : undefined;
			const rawType = cfg ? getDeviceType(cfg) : undefined;
			const label = rawType
				? (deviceTypesMap[rawType] ?? rawType)
				: $t('overview.unknown-device-type');
			counts.set(label, (counts.get(label) ?? 0) + 1);
		}
		return Array.from(counts.entries())
			.sort((a, b) => b[1] - a[1])
			.map(([label, value], i) => ({ label, value, color: PALETTE[i % PALETTE.length] }));
	});

	const max = $derived(bars.reduce((m, b) => Math.max(m, b.value), 0));
</script>

<div class="ds-card-pad">
	{#if !bars.length}
		<p class="text-sm" style="color: var(--ds-text-dim)">
			{$t('overview.device-types.no-data')}
		</p>
	{:else}
		<div class="space-y-2">
			{#each bars as b (b.label)}
				<div>
					<div class="mb-1 flex items-baseline justify-between text-xs">
						<span class="truncate" style="color: var(--ds-text)">{b.label}</span>
						<span style="color: var(--ds-text-dim)">{b.value}</span>
					</div>
					<div
						class="h-2.5 w-full overflow-hidden rounded-full"
						style="background: var(--ds-border)"
					>
						<div
							class="h-full rounded-full"
							style="width: {max ? (b.value / max) * 100 : 0}%; background: {b.color}"
						></div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
