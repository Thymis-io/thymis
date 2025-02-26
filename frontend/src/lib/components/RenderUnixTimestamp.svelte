<script lang="ts">
	export let timestamp: string | undefined | null;

	let date: Date;

	$: date = new Date(Date.parse(timestamp));

	let clazz = '';
	export { clazz as class };
</script>

{#if timestamp && date}
	<span title={date.toISOString()} class="playwright-snapshot-unstable {clazz}">
		<time datetime={date.toISOString()}>
			{date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'long' })}
		</time>
	</span>
{/if}
