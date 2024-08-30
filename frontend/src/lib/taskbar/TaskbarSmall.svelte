<script lang="ts">
	import { t } from 'svelte-i18n';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';

	$: pendingTasks = $taskStatus.filter((task) => task.state === 'pending');
	$: runningTasks = $taskStatus.filter((task) => task.state === 'running');
	$: completedTasks = $taskStatus.filter((task) => task.state === 'completed');
	$: failedTasks = $taskStatus.filter((task) => task.state === 'failed');
	$: lastestTask = $taskStatus[$taskStatus.length - 1];
</script>

<div
	class="w-full h-full flex px-2 gap-4 lg:gap-10 justify-end items-center pr-16 bg-gray-50 dark:bg-gray-700"
>
	<div class="flex items-center gap-2">
		<PendingIcon size={20} />
		<span class="text-xs lg:text-sm">{$t('taskbar.pending')}: {pendingTasks.length}</span>
	</div>
	<div class="flex items-center gap-1 lg:gap-2">
		<RunningIcon size={20} />
		<span class="text-xs lg:text-sm">{$t('taskbar.running')}: {runningTasks.length}</span>
	</div>
	<div class="flex items-center gap-1 lg:gap-2">
		<CompletedIcon size={20} />
		<span class="text-xs lg:text-sm">{$t('taskbar.completed')}: {completedTasks.length}</span>
	</div>
	<div class="flex items-center gap-1 lg:gap-2">
		<FailedIcon size={18} />
		<span class="text-xs lg:text-sm">{$t('taskbar.failed')}: {failedTasks.length}</span>
	</div>
	<div class="flex items-center gap-1 lg:gap-2">
		{#if lastestTask}
			<span class="text-xs lg:text-sm">
				{$t('taskbar.latest-task')}: {lastestTask.display_name}, {lastestTask.state}
			</span>
		{/if}
	</div>
</div>
