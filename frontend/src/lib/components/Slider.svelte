<script lang="ts">
	export let value: number;
	export let min: number | undefined;
	export let max: number | undefined;
	export let step: number | undefined;

	export let onChange: (value: number) => void;

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
	on:change={(e) => internalOnChange(e)}
	class="range my-4 w-full"
/>

<style>
	.range {
		background: transparent;
	}
</style>
