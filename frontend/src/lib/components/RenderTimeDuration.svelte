<script lang="ts">
	interface Props {
		start: string | undefined;
		end: string | undefined;
		class?: string;
	}

	let { start, end, class: clazz = '' }: Props = $props();

	let startDate = $derived(new Date(Date.parse(start)));
	let endDate = $derived(new Date(Date.parse(end)));
	let seconds = $derived(Math.max(0, Math.floor((endDate.getTime() - startDate.getTime()) / 1000)));
	let timeDuration = $derived((seconds: number) => {
		const hours = Math.floor(seconds / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		const secs = seconds % 60;

		return `${hours}h ${minutes}m ${secs}s`;
	});
</script>

{#if seconds}
	<span title={timeDuration(seconds)} class="playwright-snapshot-unstable {clazz}">
		{timeDuration(seconds)}
	</span>
{/if}
