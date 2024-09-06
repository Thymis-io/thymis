<script lang="ts">
	import { t } from 'svelte-i18n';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import TaskbarIcon from './TaskbarIcon.svelte';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';
	import { Tooltip } from 'flowbite-svelte';

	$: pendingTasks = $taskStatus.filter((task) => task.state === 'pending');
	$: runningTasks = $taskStatus.filter((task) => task.state === 'running');
	$: completedTasks = $taskStatus.filter((task) => task.state === 'completed');
	$: failedTasks = $taskStatus.filter((task) => task.state === 'failed');
	$: lastestTask = $taskStatus[$taskStatus.length - 1];
</script>

<div
	class="w-full h-full flex px-2 gap-2 sm:gap-4 xl:gap-10 pr-8 md:pr-16 justify-end items-center bg-gray-50 dark:bg-gray-700"
>
	<TaskbarIcon title={$t('taskbar.pending')} tasks={pendingTasks}>
		<PendingIcon size={20} slot="icon" class="w-full" />
	</TaskbarIcon>
	<TaskbarIcon title={$t('taskbar.running')} tasks={runningTasks}>
		<RunningIcon size={20} slot="icon" class="w-full" />
	</TaskbarIcon>
	<TaskbarIcon title={$t('taskbar.completed')} tasks={completedTasks}>
		<CompletedIcon size={20} slot="icon" class="w-full" />
	</TaskbarIcon>
	<TaskbarIcon title={$t('taskbar.failed')} tasks={failedTasks}>
		<FailedIcon size={20} slot="icon" class="w-full" />
	</TaskbarIcon>
	<div class="flex items-center gap-1 lg:gap-2 lg:ml-2">
		{#if lastestTask}
			<span class="text-xs md:text-sm mr-1">
				{$t('taskbar.latest-task')}:
			</span>
			<span class="text-xs md:text-sm truncate max-w-64">
				{lastestTask.display_name}
			</span>
			<Tooltip class="max-w-[100vw]">{lastestTask.display_name}</Tooltip>
			<span class="text-xs md:text-sm">
				({lastestTask.state})
			</span>
		{/if}
	</div>
</div>
