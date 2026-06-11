<script lang="ts">
	import { t } from 'svelte-i18n';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import TaskbarIcon from './TaskbarIcon.svelte';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/play';
	import CompletedIcon from 'lucide-svelte/icons/check';
	import FailedIcon from 'lucide-svelte/icons/ban';
	import { page } from '$app/stores';
	import Paginator from '$lib/components/Paginator.svelte';
	import { queryParameters } from 'sveltekit-search-params';
	import TaskbarName from './TaskbarName.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';

	interface Props {
		globalState: GlobalState;
		deploymentInfos: DeploymentInfo[];
		inPlaywright: boolean;
	}

	let { globalState, deploymentInfos, inPlaywright }: Props = $props();

	const tasks = $derived(Object.values($taskStatus));
	const pendingTasks = $derived(tasks.filter((task) => task.state === 'pending'));
	const runningTasks = $derived(tasks.filter((task) => task.state === 'running'));
	const completedTasks = $derived(tasks.filter((task) => task.state === 'completed'));
	const failedTasks = $derived(tasks.filter((task) => task.state === 'failed'));
	const latestTask = $derived(tasks.sort((a, b) => (a.start_time < b.start_time ? 1 : -1))[0]);

	const params = queryParameters();
	let currentPage = $derived(params['task-page']);

	const switchPage = async (page: number) => {
		params['task-page'] = page.toString();
	};

	const versionInfo: {
		version: string;
		headRev: string;
		dirty: boolean;
	} = __THYMIS_PACKAGE_VERSION__; // ts-ignore

	const shortRev = inPlaywright ? '00000000' : versionInfo.headRev.slice(0, 8);
</script>

<div
	class="w-full h-full flex px-3 gap-2 sm:gap-4 xl:gap-10 pr-8 md:pr-16 items-center overflow-y-auto border-t bg-[var(--ds-surface)] border-[var(--ds-border)] text-[var(--ds-text)]"
>
	<div class="text-xs md:text-sm playwright-snapshot-unstable">
		<span class="hidden xl:block min-w-[14rem]">
			{$t('taskbar.version', { values: { version: versionInfo.version } })}
			(<span class="font-mono">
				{shortRev}
			</span>{versionInfo.dirty ? '-dirty' : ''})
		</span>
		<span class="block xl:hidden">
			{$t('taskbar.version-short', { values: { version: versionInfo.version } })}
			(<span class="font-mono">
				{shortRev}
			</span>{versionInfo.dirty ? '-dirty' : ''})
		</span>
	</div>
	<TaskbarIcon class="hidden md:flex ml-auto" title={$t('taskbar.pending')} tasks={pendingTasks}>
		{#snippet icon()}
			<PendingIcon size={20} class="w-full" />
		{/snippet}
	</TaskbarIcon>
	<TaskbarIcon class="hidden md:flex" title={$t('taskbar.running')} tasks={runningTasks}>
		{#snippet icon()}
			<RunningIcon size={20} class="w-full" />
		{/snippet}
	</TaskbarIcon>
	<TaskbarIcon class="hidden md:flex" title={$t('taskbar.completed')} tasks={completedTasks}>
		{#snippet icon()}
			<CompletedIcon size={20} class="w-full" />
		{/snippet}
	</TaskbarIcon>
	<TaskbarIcon class="hidden md:flex" title={$t('taskbar.failed')} tasks={failedTasks}>
		{#snippet icon()}
			<FailedIcon size={20} class="w-full" />
		{/snippet}
	</TaskbarIcon>
	<div class="flex items-center gap-1 lg:gap-2 lg:ml-2">
		{#if latestTask}
			<span class="text-xs md:text-sm">
				{$t('taskbar.latest-task')}:
			</span>
			<span class="text-xs md:text-sm truncate max-w-64">
				<TaskbarName {globalState} {deploymentInfos} task={latestTask} />
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
