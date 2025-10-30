<script lang="ts">
	import { run } from 'svelte/legacy';
	import { onMount } from 'svelte';
	import { t } from 'svelte-i18n';
	import { calcTimeSince } from '$lib/hardwareDevices';

	let currentDate = $state(new Date());
	let date: Date | undefined = $state();

	onMount(() => {
		const interval = setInterval(() => {
			currentDate = new Date();
		}, 500);

		return () => clearInterval(interval);
	});

	interface Props {
		timestamp: string | undefined | null;
		minSeconds?: number;
		class?: string;
	}

	let { timestamp, minSeconds = 0, class: clazz = '' }: Props = $props();

	run(() => {
		if (timestamp) {
			const timeZoneAwareTimestamp = timestamp.includes('+') ? timestamp : timestamp + '+0000';
			date = new Date(Date.parse(timeZoneAwareTimestamp));
		} else {
			date = undefined;
		}
	});
</script>

{#if date}
	<span
		title={date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'long' })}
		class="playwright-snapshot-unstable {clazz}"
	>
		<time datetime={date.toISOString()}>
			{calcTimeSince(date, currentDate, minSeconds)}
		</time>
	</span>
{/if}
