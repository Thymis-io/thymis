<script lang="ts">
	export let timestamp: string | undefined | null;

	let date: Date;

	$: date = new Date(Date.parse(timestamp));
</script>

{#if timestamp && date}
	<p title={date.toISOString()} class="playwright-snapshot-unstable">
		<time datetime={date.toISOString()}>
			{date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'long' })}
		</time>
	</p>
{/if}
