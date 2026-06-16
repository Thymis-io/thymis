<script lang="ts">
	import { t } from 'svelte-i18n';
	import { RANGE_OPTIONS, type TimeRange } from '$lib/fleet';

	interface Props {
		value: TimeRange | 'custom';
		customHours?: number;
		onSelect: (range: TimeRange) => void;
		onCustom?: (hours: number) => void;
	}
	let { value, customHours = 720, onSelect, onCustom }: Props = $props();

	// customHours is part of the component contract (used by consumers to reflect the
	// current custom window); it is intentionally not consumed inside this template.
	void customHours;

	let showCustom = $state(false);
	let fromDate = $state('');
	let toDate = $state('');

	function applyCustom() {
		if (!fromDate || !toDate || !onCustom) return;
		const hours = (new Date(toDate).getTime() - new Date(fromDate).getTime()) / 3_600_000;
		if (hours > 0) onCustom(hours);
		showCustom = false;
	}
</script>

<div class="flex flex-wrap items-center gap-1">
	{#each RANGE_OPTIONS as r}
		<button
			class="ds-btn ds-btn-sm {value === r ? 'ds-btn-primary' : ''}"
			onclick={() => onSelect(r)}
		>
			{r}
		</button>
	{/each}
	{#if onCustom}
		<button
			class="ds-btn ds-btn-sm {value === 'custom' ? 'ds-btn-primary' : ''}"
			onclick={() => (showCustom = !showCustom)}
		>
			{$t('overview.range.custom')}
		</button>
	{/if}
</div>

{#if showCustom}
	<div class="mt-2 flex flex-wrap items-end gap-2">
		<label class="text-xs" style="color: var(--ds-text-dim)">
			{$t('overview.range.from')}
			<input type="date" bind:value={fromDate} class="ds-input block" />
		</label>
		<label class="text-xs" style="color: var(--ds-text-dim)">
			{$t('overview.range.to')}
			<input type="date" bind:value={toDate} class="ds-input block" />
		</label>
		<button class="ds-btn ds-btn-sm ds-btn-primary" onclick={applyCustom}>
			{$t('overview.range.apply')}
		</button>
	</div>
{/if}
