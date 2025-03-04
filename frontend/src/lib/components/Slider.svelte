<script lang="ts">
	interface Props {
		value: number;
		min: number | undefined;
		max: number | undefined;
		step: number | undefined;
		onChange: (value: number) => void;
	}

	let { value = $bindable(), min, max, step, onChange }: Props = $props();

	const internalOnChange = (e: Event) => {
		onChange(parseInt((e.target as HTMLInputElement).value));
	};
</script>

<input
	type="range"
	{min}
	{max}
	{step}
	bind:value
	onchange={(e) => internalOnChange(e)}
	class="range my-4 w-full"
/>

<style>
	.range {
		background: transparent;
	}
</style>
