<script lang="ts">
	export let timestamp: string | null;

	let date: Date;

	$: date = new Date(Date.parse(timestamp));
</script>

{#if timestamp && date}
	<time datetime={date.toISOString()}>
		{date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
	</time>
{/if}
