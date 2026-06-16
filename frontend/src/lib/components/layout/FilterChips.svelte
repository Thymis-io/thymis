<script lang="ts" generics="T extends string">
	type Chip = {
		value: T;
		label: string;
		/** Optional count badge shown after the label. */
		count?: number;
		/** Optional status dot (reuses `.ds-stat-dot` colors). */
		dot?: 'online' | 'warning' | 'danger' | 'offline' | 'info';
	};

	interface Props {
		chips: Chip[];
		selected: T;
		class?: string;
	}

	let { chips, selected = $bindable(), class: className = '' }: Props = $props();
</script>

<div class="ds-chip-bar {className}" role="group">
	{#each chips as chip (chip.value)}
		<button
			type="button"
			class="ds-chip {selected === chip.value ? 'active' : ''}"
			aria-pressed={selected === chip.value}
			onclick={() => (selected = chip.value)}
		>
			{#if chip.dot}<span class="ds-stat-dot {chip.dot}"></span>{/if}
			{chip.label}
			{#if chip.count !== undefined}<span class="ds-chip-count">{chip.count}</span>{/if}
		</button>
	{/each}
</div>
