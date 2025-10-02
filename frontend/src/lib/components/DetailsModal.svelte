<script lang="ts">
	import { Modal, type SizeType } from 'flowbite-svelte';

	interface Props {
		open?: boolean;
		title?: string;
		details?: string;
		size?: SizeType;
	}

	let { open = $bindable(false), title, details, size = 'lg' }: Props = $props();
</script>

<Modal bind:open {title} {size}>
	<span class="whitespace-pre">{details}</span>
</Modal>
