<script lang="ts">
	import { t } from 'svelte-i18n';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import TaskbarIcon from './TaskbarIcon.svelte';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';
	import { Tooltip } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import Paginator from '$lib/components/Paginator.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import TaskbarName from './TaskbarName.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';

	export let inPlaywright: boolean = false;

	$: pendingTasks = Object.values($taskStatus).filter((task) => task.state === 'pending');
	$: runningTasks = Object.values($taskStatus).filter((task) => task.state === 'running');
	$: completedTasks = Object.values($taskStatus).filter((task) => task.state === 'completed');
	$: failedTasks = Object.values($taskStatus).filter((task) => task.state === 'failed');
	$: latestTask = Object.values($taskStatus).sort((a, b) =>
		a.start_time < b.start_time ? 1 : -1
	)[0];

	let currentPageParam = queryParam('task-page');
	let currentPage = $currentPageParam;

	const switchPage = async (page: number) => {
		currentPage = page.toString();
		currentPageParam.set(currentPage);
	};

	const versionInfo: {
		version: string;
		headRev: string;
		dirty: boolean;
	} = __THYMIS_PACKAGE_VERSION__; // ts-ignore
</script>

<div
	class="border-2 dark:border-0 w-full h-full flex px-2 gap-2 sm:gap-4 xl:gap-10 pr-8 md:pr-16 items-center bg-gray-50 dark:bg-gray-700 overflow-y-auto"
>
	<!-- svelte-ignore missing-declaration -->
	<div class="text-xs md:text-sm playwright-snapshot-unstable">
		<span class="hidden lg:inline">{$t('taskbar.version')}: </span><span class="lg:hidden">v</span
		>{versionInfo.version} (<span class="font-mono"
			>{#if inPlaywright}00000000{:else}{versionInfo.headRev.slice(0, 8)}{/if}</span
		>{versionInfo.dirty ? '-dirty' : ''})
	</div>
	<TaskbarIcon class="ml-auto" title={$t('taskbar.pending')} tasks={pendingTasks}>
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
				<TaskbarName task={latestTask} />
			</span>
			<span class="text-xs md:text-sm">
				<TaskbarStatus task={latestTask} showText={false} showProgress={false} />
			</span>
		{/if}
	</div>
	<Paginator
		totalCount={$page.data.totalTaskCount}
		pageSize={$page.data.tasksPerPage}
		page={parseInt(currentPage ?? '1')}
		onChange={(page) => switchPage(page)}
	/>
</div>
