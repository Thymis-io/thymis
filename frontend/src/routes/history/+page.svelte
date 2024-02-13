<script lang="ts">
	import type { PageData } from './$types';
	export let data: PageData;
</script>

{#await data.history}
	<p>Loading...</p>
{:then history}
	{#each history as h}
		<p>{h.message}</p>
	{/each}
{/await}
