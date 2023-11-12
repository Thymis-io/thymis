<script lang="ts">
	import { SlideToggle } from '@skeletonlabs/skeleton';
	export let name: string;
	export let value: boolean = false;
</script>

<SlideToggle size="sm" {name} bind:checked={value} />
