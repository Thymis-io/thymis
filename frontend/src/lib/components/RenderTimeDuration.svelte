<script lang="ts">
	export let start: string | undefined;
	export let end: string | undefined;

	$: startDate = new Date(Date.parse(start));
	$: endDate = new Date(Date.parse(end));

	$: seconds = Math.max(0, Math.floor((endDate.getTime() - startDate.getTime()) / 1000));

	$: console.log(startDate, endDate, seconds);

	$: timeDuration = (seconds: number) => {
		const hours = Math.floor(seconds / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;

		return `${hours}h ${minutes}m ${secs}s`;
	};
</script>

{#if seconds}
	<p title={timeDuration(seconds)} class="playwright-snapshot-unstable">
		{timeDuration(seconds)}
	</p>
{/if}
