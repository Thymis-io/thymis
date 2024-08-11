<script lang="ts">
	export let timestamp: number;

	let date: Date;

	$: date = new Date(timestamp * 1000);
</script>

{#if date}
	<time datetime={date.toISOString()}>{date.toLocaleString()}</time>
{/if}
