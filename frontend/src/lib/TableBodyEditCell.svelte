<script lang="ts">
	import Pen from 'lucide-svelte/icons/pen';
	import { TableBodyCell, Input } from 'flowbite-svelte';
	import clickOutside from 'svelte-outside-click';

	export let value: string;
	export let onEnter: (() => void) | null = null;

	let isEditing: boolean = false;
</script>

<TableBodyCell>
	<div class="flex justify-between gap-2" use:clickOutside={() => (isEditing = false)}>
		{#if isEditing}
			<Input
				class="w-full"
				bind:value
				on:blur={() => onEnter?.()}
				on:keypress={(e) => {
					if (e.key === 'Enter') {
						isEditing = false;
						onEnter?.();
					}
				}}
			/>
		{:else}
			<span class="w-full p-[11px]">{value}</span>
		{/if}
		<button class="btn ml-2" on:click={() => (isEditing = !isEditing)}>
			<Pen size="20" />
		</button>
	</div>
</TableBodyCell>
