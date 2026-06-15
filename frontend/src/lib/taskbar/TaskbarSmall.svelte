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
	import type { DeploymentInfo } from '$lib/deploymentInfo';

	interface Props {
		globalState: GlobalState;
		deploymentInfos: DeploymentInfo[];
		inPlaywright: boolean;
	}

	let { globalState, deploymentInfos, inPlaywright }: Props = $props();

	// Completed/failed counts ("the calculation below") cover the last 24h only.
	const TASK_WINDOW_MS = 24 * 60 * 60 * 1000;

	const tasks = $derived(Object.values($taskStatus));
	const recentTasks = $derived(
		tasks.filter((task) => new Date(task.start_time).getTime() >= Date.now() - TASK_WINDOW_MS)
	);
	// Pending/running reflect current activity, so they are not time-bounded.
	const pendingTasks = $derived(tasks.filter((task) => task.state === 'pending'));
	const runningTasks = $derived(tasks.filter((task) => task.state === 'running'));
	const completedTasks = $derived(recentTasks.filter((task) => task.state === 'completed'));
	const failedTasks = $derived(recentTasks.filter((task) => task.state === 'failed'));
	const latestTask = $derived([...tasks].sort((a, b) => (a.start_time < b.start_time ? 1 : -1))[0]);

	const primaryRunning = $derived(runningTasks[0]);

	const progressScalingFunction = (done: number, expected: number) => {
		const f = (x: number) => x * x + 1;
		if (done === 0 || expected === 0) return 0;
		return Math.min(1, f(done) / f(expected)) * 100;
	};
	const progress = $derived.by(() => {
		const ns = primaryRunning?.nix_status;
		if (!ns) return null;
		return progressScalingFunction(ns.done, ns.expected);
	});

	const idleSummary = $derived(
		[
			failedTasks.length > 0
				? {
						text: $t('taskbar.activity.summary-failed', { values: { count: failedTasks.length } }),
						tone: 'danger'
					}
				: null,
			completedTasks.length > 0
				? {
						text: $t('taskbar.activity.summary-done', { values: { count: completedTasks.length } }),
						tone: 'mute'
					}
				: null
		].filter((p): p is { text: string; tone: string } => p !== null)
	);

	const activeCounts = $derived(
		[
			runningTasks.length > 0
				? {
						text: $t('taskbar.activity.summary-running', {
							values: { count: runningTasks.length }
						}),
						tone: 'accent'
					}
				: null,
			pendingTasks.length > 0
				? {
						text: $t('taskbar.activity.summary-pending', {
							values: { count: pendingTasks.length }
						}),
						tone: 'warning'
					}
				: null,
			failedTasks.length > 0
				? {
						text: $t('taskbar.activity.summary-failed', { values: { count: failedTasks.length } }),
						tone: 'danger'
					}
				: null
		].filter((p): p is { text: string; tone: string } => p !== null)
	);

	const isActive = $derived(runningTasks.length > 0 || pendingTasks.length > 0);

	const versionInfo: {
		version: string;
		headRev: string;
		dirty: boolean;
	} = __THYMIS_PACKAGE_VERSION__; // ts-ignore

	const shortRev = inPlaywright ? '00000000' : versionInfo.headRev.slice(0, 8);
</script>

<!-- overflow-hidden (not auto): the bar must never show a horizontal scrollbar.
     The flexible activity block in the middle truncates instead. -->
<div
	class="w-full h-full flex items-center px-4 gap-4 pr-8 md:pr-16 overflow-hidden border-t bg-[var(--ds-surface)] border-[var(--ds-border)] text-[var(--ds-text)]"
>
	<div class="flex flex-col justify-center min-w-0 flex-1 leading-tight">
		<div class="flex items-center gap-2 min-w-0 text-sm">
			{#if runningTasks.length > 0}
				<RunningIcon size={16} class="shrink-0 animate-spin text-[var(--ds-accent)]" />
				<span class="flex items-center min-w-0 max-w-[16rem] lg:max-w-[24rem] overflow-hidden">
					<TaskbarName {globalState} {deploymentInfos} task={primaryRunning} iconSize={15} />
				</span>
				{#if progress !== null}
					<span class="ds-mini-progress shrink-0" aria-hidden="true">
						<span style="width: {progress}%"></span>
					</span>
					<span class="shrink-0 text-xs tabular-nums text-[var(--ds-text-mute)]">
						{Math.round(progress)}%
					</span>
				{/if}
				{#if runningTasks.length > 1}
					<span class="shrink-0 text-xs text-[var(--ds-text-mute)]">
						{$t('taskbar.activity.more', { values: { count: runningTasks.length - 1 } })}
					</span>
				{/if}
			{:else if pendingTasks.length > 0}
				<PendingIcon size={16} class="shrink-0 text-[var(--ds-warning)]" />
				<span class="font-medium whitespace-nowrap">{$t('taskbar.activity.pending-waiting')}</span>
			{:else}
				<span class="ds-stat-dot {failedTasks.length > 0 ? 'danger' : 'online'} shrink-0"></span>
				<span class="font-medium whitespace-nowrap">
					{idleSummary.length > 0
						? $t('taskbar.activity.nothing-running')
						: $t('taskbar.activity.all-clear')}
				</span>
				{#if idleSummary.length > 0}
					<span class="text-[var(--ds-text-mute)]">·</span>
					{#each idleSummary as part, i}
						<span
							class={part.tone === 'danger'
								? 'text-[var(--ds-danger)] font-semibold'
								: 'text-[var(--ds-text-mute)]'}
							>{part.text}{#if i < idleSummary.length - 1},{/if}</span
						>
					{/each}
				{/if}
			{/if}
		</div>

		<div
			class="flex items-center gap-2 text-xs text-[var(--ds-text-mute)] overflow-hidden whitespace-nowrap"
		>
			{#if isActive}
				{#each activeCounts as part, i}
					{#if i > 0}<span class="opacity-50">·</span>{/if}
					<span class="ds-count {part.tone}">{part.text}</span>
				{/each}
			{:else if latestTask}
				<span class="shrink-0">{$t('taskbar.latest-task')}:</span>
				<span class="flex items-center min-w-0 max-w-[14rem] lg:max-w-[22rem] overflow-hidden">
					<TaskbarName {globalState} {deploymentInfos} task={latestTask} iconSize={13} />
				</span>
				<span class="shrink-0 scale-90 origin-left">
					<TaskbarStatus task={latestTask} showProgress={false} />
				</span>
				<span class="opacity-50 shrink-0">·</span>
				<RenderTimeAgo class="shrink-0" timestamp={latestTask.start_time} minSeconds={1} />
			{/if}
		</div>
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
	.ds-count.danger {
		color: var(--ds-danger);
	}
</style>
