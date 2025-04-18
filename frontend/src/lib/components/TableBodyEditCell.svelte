<script lang="ts">
	import Pen from 'lucide-svelte/icons/pen';
	import { TableBodyCell, Input } from 'flowbite-svelte';
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

<TableBodyCell tdClass="p-2 px-2 md:px-4">
	<div class="flex gap-4 p-0" use:clickOutside={() => (isEditing = false)}>
		{#if isEditing}
			<Input
				class="w-full min-w-32"
				size="sm"
				bind:value
				on:blur={() => onEnter?.(value)}
				on:keypress={(e) => {
					if (e.key === 'Enter') {
						isEditing = false;
						onEnter?.(value);
					}
				}}
			/>
		{:else if children}
			{@render children?.()}
		{:else}
			<span class="p-0">{value}</span>
		{/if}
		<button onclick={() => (isEditing = !isEditing)}>
			<Pen size={'1rem'} class="min-w-4" />
		</button>
	</div>
	{@render bottom?.({ value })}
</TableBodyCell>
