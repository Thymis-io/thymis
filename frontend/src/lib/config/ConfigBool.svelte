<script lang="ts">
	import { SlideToggle } from '@skeletonlabs/skeleton';

	export let name: string;
	export let value: boolean | undefined = false;
	export let onChange: (value: boolean) => void = () => {};

	let change = (e: Event) => {
		onChange((e.target as HTMLInputElement).checked);
	};
</script>

<SlideToggle class="mt-1.5" size="sm" {name} checked={value} on:change={change} />
