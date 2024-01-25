<script lang="ts">
	import { SlideToggle } from '@skeletonlabs/skeleton';

	export let name: string;
	export let value: boolean | undefined = false;
	export let change: (value: boolean) => void = () => {};

	let changeInternal = (e: Event) => {
		change((e.target as HTMLInputElement).checked);
	};
</script>

<SlideToggle class="mt-1.5" size="sm" {name} checked={value} on:change={changeInternal} />
