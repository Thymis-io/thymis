<script lang="ts">
	import type { PageData } from "./$types";
	export let data: PageData;
</script>
{#if data.ip}
<h1>Visit Thymis UI on your end device at http://{data.ip}/</h1>
{:else}
<h1>Waiting for Thymis to connect to the network...</h1>
{/if}

<svelte:head>
{#if !data.ip}
<meta http-equiv="refresh" content="4">
{/if}
</svelte:head>
