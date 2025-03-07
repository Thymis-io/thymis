<script lang="ts">
	import type { PageData } from './$types';
	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

{#if data.ip}
	<h1>Visit Thymis UI on your end device at http://{data.ip}/</h1>
{:else}
	<h1>Waiting for Thymis to connect to the network...</h1>
{/if}

<svelte:head>
	{#if !data.ip}
		<meta http-equiv="refresh" content="4" />
	{/if}
</svelte:head>
