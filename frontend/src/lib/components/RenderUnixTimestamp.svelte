<script lang="ts">
	export let timestamp: string | null;

	let date: Date;

	$: date = new Date(Date.parse(timestamp));
</script>

{#if timestamp && date}
	<p title={date.toISOString()}>
		<time datetime={date.toISOString()}>
			{date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })}
		</time>
	</p>
{/if}
