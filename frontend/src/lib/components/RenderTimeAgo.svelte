<script lang="ts">
	import { onMount } from 'svelte';
	import { calcTimeSince } from '$lib/hardwareDevices';

	interface Props {
		timestamp: string | null;
		minSeconds?: number;
		class?: string;
	}

	let { timestamp, minSeconds = 0, class: customClass = '' }: Props = $props();

	let currentDate = $state(new Date());
	let date = $state<Date | undefined>(timestamp ? new Date(timestamp) : undefined);

	onMount(() => {
		const interval = setInterval(() => {
			currentDate = new Date();
		}, 500);

		return () => clearInterval(interval);
	});
</script>

{#if date}
	<span
		title={date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'long' })}
		class="playwright-snapshot-unstable {customClass}"
	>
		<time datetime={date.toISOString()}>
			{calcTimeSince(date, currentDate, minSeconds)}
		</time>
	</span>
{/if}
