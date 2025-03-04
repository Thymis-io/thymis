<script lang="ts">
	let date: Date = $derived(new Date(Date.parse(timestamp)));

	interface Props {
		timestamp: string | undefined | null;
		class?: string;
	}

	let { timestamp, class: clazz = '' }: Props = $props();
</script>

{#if timestamp && date}
	<span title={date.toISOString()} class="playwright-snapshot-unstable {clazz}">
		<time datetime={date.toISOString()}>
			{date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'long' })}
		</time>
	</span>
{/if}
