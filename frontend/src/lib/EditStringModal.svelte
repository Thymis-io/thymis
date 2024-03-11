<script lang="ts">
	import { Button, Modal, Label, Input, type SizeType } from 'flowbite-svelte';

	export let title: string | undefined = '';
	export let size: SizeType | undefined = 'md';
	export let label: string | undefined = '';
	export let value: string | undefined;
	export let open: boolean;
	export let onClose: (() => void) | undefined = undefined;
	export let onSave: ((value: string) => void) | undefined = undefined;
</script>

<Modal bind:title bind:open outsideclose {size} on:close={() => onClose?.()}>
	<Label>{label}</Label>
	<Input bind:value />
	<div class="flex justify-end gap-2">
		<Button color="alternative" on:click={() => onClose?.()}>Cancel</Button>
		<Button
			on:click={() => {
				onSave?.(value ?? '');
				onClose?.();
			}}
		>
			Save
		</Button>
	</div>
</Modal>
