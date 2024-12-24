<script lang="ts">
	import { t } from 'svelte-i18n';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import TaskbarIcon from './TaskbarIcon.svelte';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';
	import { Tooltip, Pagination, PaginationItem } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import { LightPaginationNav } from 'svelte-paginate';
	import { queryParam } from 'sveltekit-search-params';

	$: pendingTasks = Object.values($taskStatus).filter((task) => task.state === 'pending');
	$: runningTasks = Object.values($taskStatus).filter((task) => task.state === 'running');
	$: completedTasks = Object.values($taskStatus).filter((task) => task.state === 'completed');
	$: failedTasks = Object.values($taskStatus).filter((task) => task.state === 'failed');
	$: latestTask = Object.values($taskStatus)[Object.values($taskStatus).length - 1];

	$: currentPage = queryParam('task-page');

	const switchPage = (page: number) => {
		currentPage.set(page.toString());
	};
</script>

<div
	class="border-2 dark:border-0 w-full h-full flex px-2 gap-2 sm:gap-4 xl:gap-10 pr-8 md:pr-16 justify-end items-center bg-gray-50 dark:bg-gray-700"
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
		{#if latestTask}
			<span class="text-xs md:text-sm mr-1">
				{$t('taskbar.latest-task')}:
			</span>
			<span class="text-xs md:text-sm truncate max-w-64">
				{latestTask.task_type}
			</span>
			<Tooltip class="max-w-[100vw]">{latestTask.task_type}</Tooltip>
			<span class="text-xs md:text-sm">
				({latestTask.state})
			</span>
		{/if}
	</div>
	<LightPaginationNav
		totalItems={$page.data.totalTaskCount}
		pageSize={$page.data.tasksPerPage}
		limit={1}
		currentPage={parseInt($currentPage || '1')}
		on:setPage={(e) => switchPage(e.detail.page)}
	/>
</div>
