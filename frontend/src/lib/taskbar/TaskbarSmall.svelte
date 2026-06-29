<script lang="ts">
	import { t } from 'svelte-i18n';
	import { taskStatus } from '$lib/taskstatus';
	import PendingIcon from 'lucide-svelte/icons/clock';
	import RunningIcon from 'lucide-svelte/icons/loader-circle';
	import ListIcon from 'lucide-svelte/icons/list';
	import TaskbarName from './TaskbarName.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		inPlaywright: boolean;
	}

	let { globalState, inPlaywright }: Props = $props();

	// The bar always surfaces the latest task; running/pending counts only reflect
	// current activity, so neither is time-bounded (no 24h window anymore).
	const tasks = $derived(Object.values($taskStatus));
	const pendingTasks = $derived(tasks.filter((task) => task.state === 'pending'));
	const runningTasks = $derived(tasks.filter((task) => task.state === 'running'));
	const latestTask = $derived([...tasks].sort((a, b) => (a.start_time < b.start_time ? 1 : -1))[0]);

	const isActive = $derived(runningTasks.length > 0 || pendingTasks.length > 0);

	const progressScalingFunction = (done: number, expected: number) => {
		const f = (x: number) => x * x + 1;
		if (done === 0 || expected === 0) return 0;
		return Math.min(1, f(done) / f(expected)) * 100;
	};
	// Progress is shown for the latest task only while it is still running.
	const progress = $derived.by(() => {
		const ns = latestTask?.state === 'running' ? latestTask?.nix_status : null;
		if (!ns) return null;
		return progressScalingFunction(ns.done, ns.expected);
	});

	const versionInfo: {
		version: string;
		headRev: string;
		dirty: boolean;
	} = __THYMIS_PACKAGE_VERSION__; // ts-ignore

	const shortRev = inPlaywright ? '00000000' : versionInfo.headRev.slice(0, 8);
</script>

<!-- overflow-hidden (not auto): the bar must never show a horizontal scrollbar.
     The flexible latest-task block in the middle truncates instead. -->
<div
	class="w-full h-full flex items-center px-4 gap-4 pr-8 md:pr-16 overflow-hidden border-t bg-[var(--ds-surface)] border-[var(--ds-border)] text-[var(--ds-text)]"
>
	<!-- Single row: latest task on the left, current activity inline. -->
	<div class="flex items-center gap-2 min-w-0 flex-1 text-sm overflow-hidden">
		{#if latestTask}
			{#if latestTask.state === 'running'}
				<RunningIcon size={15} class="shrink-0 animate-spin text-[var(--ds-accent)]" />
			{/if}
			<span class="shrink-0 text-[var(--ds-text-mute)]">{$t('taskbar.latest-task')}:</span>
			<span class="flex items-center min-w-0 max-w-[14rem] lg:max-w-[22rem] overflow-hidden">
				<TaskbarName {globalState} task={latestTask} iconSize={15} />
			</span>
			<span class="shrink-0 scale-90 origin-left">
				<TaskbarStatus task={latestTask} showProgress={false} />
			</span>
			{#if progress !== null}
				<span class="ds-mini-progress shrink-0" aria-hidden="true">
					<span style="width: {progress}%"></span>
				</span>
				<span class="shrink-0 text-xs tabular-nums text-[var(--ds-text-mute)]">
					{Math.round(progress)}%
				</span>
			{/if}
			<span class="opacity-50 shrink-0">·</span>
			<RenderTimeAgo class="shrink-0" timestamp={latestTask.start_time} minSeconds={1} />
		{:else}
			<span class="ds-stat-dot online shrink-0"></span>
			<span class="font-medium whitespace-nowrap">{$t('taskbar.activity.all-clear')}</span>
		{/if}

		{#if isActive}
			<span class="opacity-50 shrink-0">·</span>
			{#if runningTasks.length > 0}
				<span class="ds-count accent shrink-0 flex items-center gap-1">
					<RunningIcon size={12} class="animate-spin" />
					{$t('taskbar.activity.summary-running', { values: { count: runningTasks.length } })}
				</span>
			{/if}
			{#if runningTasks.length > 0 && pendingTasks.length > 0}
				<span class="opacity-50 shrink-0">·</span>
			{/if}
			{#if pendingTasks.length > 0}
				<span class="ds-count warning shrink-0 flex items-center gap-1">
					<PendingIcon size={12} />
					{$t('taskbar.activity.summary-pending', { values: { count: pendingTasks.length } })}
				</span>
			{/if}
		{/if}
	</div>

	<div class="flex items-center gap-4 shrink-0">
		<span
			class="text-[11px] text-[var(--ds-text-mute)] hidden xl:block playwright-snapshot-unstable"
			title={$t('taskbar.version', { values: { version: versionInfo.version } })}
		>
			{$t('taskbar.version-short', { values: { version: versionInfo.version } })}
			(<span class="font-mono">{shortRev}</span>{versionInfo.dirty ? '-dirty' : ''})
		</span>
		<a href="/tasks" class="ds-btn ds-btn-sm whitespace-nowrap flex items-center gap-1.5">
			<ListIcon size={15} />
			{$t('taskbar.view-all')}
		</a>
	</div>
</div>

<style lang="postcss">
	.ds-mini-progress {
		display: inline-block;
		width: 5rem;
		height: 5px;
		border-radius: 999px;
		background: var(--ds-surface-2);
		overflow: hidden;
	}
	.ds-mini-progress span {
		display: block;
		height: 100%;
		border-radius: 999px;
		background: var(--ds-accent);
		transition: width 0.3s ease;
	}

	.ds-count {
		font-weight: 600;
	}
	.ds-count.accent {
		color: var(--ds-accent);
	}
	.ds-count.warning {
		color: var(--ds-warning);
	}
</style>
