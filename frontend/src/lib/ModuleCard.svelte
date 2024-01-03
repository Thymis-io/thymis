<script lang="ts">
	export let name: string;
	export let shortDescription: string;
	export let icon: string;
</script>

<div class="card p-4 flex flex-col items-center">
	<img class="h-32 w-32" src={icon} alt="icon" />
	<span class="mt-4 font-bold">{name}</span>
	<span class="mt-4 w-48 flex-1">{shortDescription}</span>
	<button class="btn mt-8 variant-filled-secondary" type="button">Install</button>
</div>
