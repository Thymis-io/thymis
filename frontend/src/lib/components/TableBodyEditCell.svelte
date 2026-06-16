<script lang="ts">
	import Pen from 'lucide-svelte/icons/pen';
	import clickOutside from 'svelte-outside-click';
	import type { Snippet } from 'svelte';

	interface Props {
		value: string;
		onEnter?: ((value: string) => void) | null;
		bottom?: import('svelte').Snippet<[any]>;
		children?: Snippet;
	}

	let { value = $bindable(), onEnter = null, bottom, children }: Props = $props();

	let isEditing: boolean = $state(false);
</script>

<td>
	<div class="flex items-center gap-2" use:clickOutside={() => (isEditing = false)}>
		{#if isEditing}
			<input
				class="ds-input min-w-32"
				bind:value
				onblur={() => onEnter?.(value)}
				onkeypress={(e) => {
					if (e.key === 'Enter') {
						isEditing = false;
						onEnter?.(value);
					}
				}}
			/>
		{:else if children}
			{@render children?.()}
		{:else}
			<span>{value}</span>
		{/if}
		<button
			type="button"
			class="ds-icon-btn"
			aria-label={isEditing ? 'Stop editing' : 'Edit'}
			onclick={() => (isEditing = !isEditing)}
		>
			<Pen size={'0.875rem'} class="min-w-4" />
		</button>
	</div>
	{@render bottom?.({ value })}
</td>
