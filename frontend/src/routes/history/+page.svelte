<script lang="ts">
	import type { PageData } from './$types';
	export let data: PageData;
</script>

{#each data.history as h}
	<p>{h.message}</p>
{/each}
