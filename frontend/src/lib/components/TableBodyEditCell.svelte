<script lang="ts">
	import Pen from 'lucide-svelte/icons/pen';
	import { TableBodyCell, Input } from 'flowbite-svelte';
	import clickOutside from 'svelte-outside-click';

	export let value: string;
	export let onEnter: ((value: string) => void) | null = null;

	let isEditing: boolean = false;
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
		{:else}
			<span class="p-0">{value}</span>
		{/if}
		<button on:click={() => (isEditing = !isEditing)}>
			<Pen size={'1rem'} class="min-w-4" />
		</button>
	</div>
	<slot name="bottom" {value} />
</TableBodyCell>
