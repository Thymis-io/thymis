<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from 'svelte-i18n';

	export let timestamp: string | undefined | null;
	export let minSeconds: number = 0;

	let currentDate = new Date();
	let date: Date | undefined;

	$: {
		if (timestamp) {
			const timeZoneAwareTimestamp = timestamp.includes('+') ? timestamp : timestamp + '+0000';
			date = new Date(Date.parse(timeZoneAwareTimestamp));
		} else {
			date = undefined;
		}
	}

	onMount(() => {
		const interval = setInterval(() => {
			currentDate = new Date();
		}, 500);

		return () => clearInterval(interval);
	});

	$: timeSince = (date: Date, currentDate: Date) => {
		const seconds = Math.max(
			minSeconds,
			Math.floor((currentDate.getTime() - date.getTime()) / 1000)
		);
		let interval = seconds / (60 * 60 * 24 * 365);
		if (interval > 1) return $t('time.ago.year', { values: { count: Math.floor(interval) } });
		interval = seconds / (60 * 60 * 24 * 30);
		if (interval > 1) return $t('time.ago.month', { values: { count: Math.floor(interval) } });
		interval = seconds / (60 * 60 * 24 * 7);
		if (interval > 1) return $t('time.ago.week', { values: { count: Math.floor(interval) } });
		interval = seconds / (60 * 60 * 24);
		if (interval > 1) return $t('time.ago.day', { values: { count: Math.floor(interval) } });
		interval = seconds / (60 * 60);
		if (interval > 1) return $t('time.ago.hour', { values: { count: Math.floor(interval) } });
		interval = seconds / 60;
		if (interval > 1) return $t('time.ago.minute', { values: { count: Math.floor(interval) } });
		return $t('time.ago.second', { values: { count: Math.floor(seconds) } });
	};
</script>

{#if date}
	<span
		title={date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'long' })}
		class="playwright-snapshot-unstable"
	>
		<time datetime={date.toISOString()}>
			{timeSince(date, currentDate)}
		</time>
	</span>
{/if}
