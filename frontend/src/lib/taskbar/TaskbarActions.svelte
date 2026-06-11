<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type TaskShort, cancelTask, retryTask } from '$lib/taskstatus';
	import { page } from '$app/stores';
	interface Props {
		task: TaskShort;
	}

	let { task }: Props = $props();
</script>

<div class="flex flex-row items-center justify-end gap-2">
	{#if task.state === 'pending' || task.state === 'running'}
		<button class="ds-btn ds-btn-sm whitespace-nowrap" onclick={() => cancelTask(task.id)}>
			{$t('taskbar.cancel')}
		</button>
	{:else if task.state === 'completed' || task.state === 'failed'}
		<button class="ds-btn ds-btn-sm whitespace-nowrap" onclick={() => retryTask(task.id)}>
			{$t('taskbar.retry')}
		</button>
	{/if}
	<a
		class="ds-btn ds-btn-sm ds-btn-primary whitespace-nowrap"
		href="/tasks/{task.id}{$page.url.search}"
	>
		{$t('taskbar.details')}
	</a>
</div>
