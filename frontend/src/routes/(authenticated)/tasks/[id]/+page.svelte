<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import RenderTimeDuration from '$lib/components/RenderTimeDuration.svelte';
	import {
		subscribedTask,
		subscribeTask,
		cancelTask,
		retryTask,
		type Task,
		type TaskShort,
		type TaskProcess
	} from '$lib/taskstatus';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import Section from '$lib/components/layout/Section.svelte';
	import TaskbarName from '$lib/taskbar/TaskbarName.svelte';
	import TaskbarStatus from '$lib/taskbar/TaskbarStatus.svelte';
	import Copy from 'lucide-svelte/icons/copy';
	import Check from 'lucide-svelte/icons/check';
	import AlertTriangle from 'lucide-svelte/icons/triangle-alert';
	import Repeat from 'lucide-svelte/icons/repeat';
	import X from 'lucide-svelte/icons/x';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let task: Task | undefined = $derived(!$subscribedTask ? data.task : $subscribedTask);

	const cleanStdOut = (stdoutorerr: string) => stdoutorerr.replaceAll('\r[K', '');
	const escapeForDoubleQuotes = (str: string) => str.replaceAll(/["`\\$]/g, '\\$&');
	const needsDoubleQuotes = (str: string) =>
		str !== escapeForDoubleQuotes(str) || str.includes(' ');

	const buildCommand = (process: TaskProcess) => {
		if (!process.process_program || !process.process_args) return null;
		const env = process.process_env
			? Object.entries(process.process_env)
					.map(([key, value]) => `${key}="${escapeForDoubleQuotes(value)}"`)
					.join(' ') + ' '
			: '';
		const args = process.process_args
			.map((arg) => (needsDoubleQuotes(arg) ? `"${escapeForDoubleQuotes(arg)}"` : arg))
			.join(' ');
		return env + process.process_program + ' ' + args;
	};

	const processHasOutput = (process: TaskProcess) =>
		!!(
			process.process_stdout ||
			process.process_stderr ||
			process.nix_errors?.length ||
			process.nix_error_logs?.length ||
			process.nix_warning_logs?.length ||
			process.nix_notice_logs?.length ||
			process.nix_info_logs?.length
		);

	let copiedId = $state(false);
	const copyId = () => {
		if (!task) return;
		navigator.clipboard.writeText(task.id);
		copiedId = true;
		setTimeout(() => (copiedId = false), 2000);
	};

	let selectedProcess = $state(0);
	// Clamp selection if the process list changes (e.g. while running).
	let activeProcess = $derived(
		task?.processes && task.processes.length > 0
			? Math.min(selectedProcess, task.processes.length - 1)
			: 0
	);

	$effect(() => {
		subscribeTask(data.task_id);
	});
</script>

{#snippet logBlock(title: string, code: string)}
	<div>
		<h4 class="log-label">{title}</h4>
		<MonospaceText {code} />
	</div>
{/snippet}

{#snippet processContent(process: TaskProcess)}
	{@const command = buildCommand(process)}
	<div class="flex flex-col gap-4">
		<div>
			<h4 class="log-label">{$t('task-details.command')}</h4>
			{#if command}
				<MonospaceText code={command} />
			{:else}
				<p class="muted-note">{$t('task-details.no-command')}</p>
			{/if}
		</div>

		{#if process.nix_errors && process.nix_errors.length > 0}
			{@render logBlock(
				$t('task-details.nix-errors'),
				process.nix_errors.map((error) => error.msg).join('\n')
			)}
		{/if}
		{#if process.nix_error_logs && process.nix_error_logs.length > 0}
			{@render logBlock($t('task-details.nix-errors'), process.nix_error_logs.join('\n'))}
		{/if}
		{#if process.nix_warning_logs && process.nix_warning_logs.length > 0}
			{@render logBlock($t('task-details.nix-warnings'), process.nix_warning_logs.join('\n'))}
		{/if}
		{#if process.nix_notice_logs && process.nix_notice_logs.length > 0}
			{@render logBlock($t('task-details.nix-notices'), process.nix_notice_logs.join('\n'))}
		{/if}
		{#if process.nix_info_logs && process.nix_info_logs.length > 0}
			{@render logBlock($t('task-details.nix-infos'), process.nix_info_logs.join('\n'))}
		{/if}
		{#if process.process_stdout}
			{@render logBlock($t('task-details.stdout'), cleanStdOut(process.process_stdout))}
		{/if}
		{#if process.process_stderr}
			{@render logBlock($t('task-details.stderr'), cleanStdOut(process.process_stderr))}
		{/if}

		{#if !processHasOutput(process)}
			<p class="muted-note">{$t('task-details.no-output')}</p>
		{/if}
	</div>
{/snippet}

<PageHead>
	{#snippet children()}
		{#if task}
			<div class="ds-page-title flex min-w-0 items-center">
				<TaskbarName
					globalState={data.globalState}
					deploymentInfos={data.deploymentInfos}
					task={task as TaskShort}
					iconSize={22}
				/>
			</div>
			<TaskbarStatus task={task as TaskShort} showProgress={false} />
		{/if}
	{/snippet}

	{#snippet actions()}
		{#if task && (task.state === 'pending' || task.state === 'running')}
			<button class="ds-btn" onclick={() => cancelTask(task.id)}>
				<X size={'1rem'} class="min-w-4" />
				<span class="whitespace-nowrap">{$t('taskbar.cancel')}</span>
			</button>
		{:else if task && (task.state === 'completed' || task.state === 'failed')}
			<button class="ds-btn" onclick={() => retryTask(task.id)}>
				<Repeat size={'1rem'} class="min-w-4" />
				<span class="whitespace-nowrap">{$t('taskbar.retry')}</span>
			</button>
		{/if}
	{/snippet}
</PageHead>

{#if task}
	<div class="flex flex-col gap-4">
		<!-- Overview: full-width metadata bar -->
		<Section title={$t('task-details.overview')}>
			<div class="meta">
				<div class="meta-item">
					<span class="meta-key">{$t('taskbar.status')}</span>
					<span class="meta-val"
						><TaskbarStatus task={task as TaskShort} showProgress={false} /></span
					>
				</div>
				<div class="meta-item">
					<span class="meta-key">{$t('task-details.task-id')}</span>
					<span class="meta-val mono flex items-center gap-2">
						{task.id}
						<button class="id-copy" onclick={copyId} title={$t('task-details.copy')}>
							{#if copiedId}
								<Check size={14} style="color: var(--ds-success)" />
							{:else}
								<Copy size={14} />
							{/if}
						</button>
					</span>
				</div>
				<div class="meta-item">
					<span class="meta-key">{$t('task-details.started')}</span>
					<span class="meta-val">
						<RenderUnixTimestamp timestamp={task.start_time} />
						<span class="muted-note"
							>(<RenderTimeAgo timestamp={task.start_time} minSeconds={1} />)</span
						>
					</span>
				</div>
				<div class="meta-item">
					<span class="meta-key">{$t('task-details.ended')}</span>
					<span class="meta-val">
						{#if task.end_time}
							<RenderUnixTimestamp timestamp={task.end_time} />
						{:else}
							<span class="muted-note">{$t('task-details.still-running')}</span>
						{/if}
					</span>
				</div>
				<div class="meta-item">
					<span class="meta-key">{$t('taskbar.duration')}</span>
					<span class="meta-val">
						{#if task.end_time}
							<RenderTimeDuration start={task.start_time} end={task.end_time} />
						{:else}
							<span class="muted-note">—</span>
						{/if}
					</span>
				</div>
				{#if task.parent_task_id}
					<div class="meta-item">
						<span class="meta-key">{$t('task-details.parent')}</span>
						<span class="meta-val mono">
							<a class="ds-link" href="/tasks/{task.parent_task_id}">{task.parent_task_id}</a>
						</span>
					</div>
				{/if}
				{#if task.children && task.children.length > 0}
					<div class="meta-item">
						<span class="meta-key">{$t('task-details.subtasks')}</span>
						<span class="meta-val mono flex flex-col gap-1">
							{#each task.children as child (child)}
								<a class="ds-link" href="/tasks/{child}">{child}</a>
							{/each}
						</span>
					</div>
				{/if}
			</div>
		</Section>

		{#if task.exception}
			<Section title={$t('task-details.exception')} class="exception-card">
				{#snippet header()}
					<AlertTriangle size={16} style="color: var(--ds-danger)" />
				{/snippet}
				<MonospaceText code={task.exception} />
			</Section>
		{/if}

		<Section title={$t('task-details.submission-data')}>
			<MonospaceText
				code={JSON.stringify(task.task_submission_data || task.task_submission_data_raw, null, 2)}
				language={undefined}
			/>
		</Section>

		<Section title={$t('task-details.processes')}>
			{#if task.processes && task.processes.length > 0}
				{#if task.processes.length > 1}
					<div class="proc-tabs" role="tablist">
						{#each task.processes as process, i (process.process_index)}
							{@const hasError = !!(process.nix_errors?.length || process.nix_error_logs?.length)}
							<button
								type="button"
								role="tab"
								aria-selected={activeProcess === i}
								class="proc-tab"
								class:active={activeProcess === i}
								onclick={() => (selectedProcess = i)}
							>
								{$t('task-details.process', { values: { n: i + 1 } })}
								{#if hasError}
									<span class="proc-dot" title={$t('task-details.nix-errors')}></span>
								{/if}
							</button>
						{/each}
					</div>
				{/if}
				{@render processContent(task.processes[activeProcess])}
			{:else}
				<p class="muted-note">{$t('task-details.no-processes')}</p>
			{/if}
		</Section>
	</div>
{/if}

<style lang="postcss">
	.log-label {
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--ds-text-mute);
		margin-bottom: 6px;
	}
	.muted-note {
		font-size: 13px;
		color: var(--ds-text-mute);
	}
	/* full-width horizontal metadata bar */
	.meta {
		display: flex;
		flex-wrap: wrap;
		gap: 14px 40px;
	}
	.meta-item {
		display: flex;
		flex-direction: column;
		gap: 4px;
		min-width: 0;
	}
	.meta-key {
		font-size: 11.5px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--ds-text-mute);
	}
	.meta-val {
		font-size: 13px;
		color: var(--ds-text);
	}
	.id-copy {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 3px;
		border-radius: 5px;
		color: var(--ds-text-mute);
		flex-shrink: 0;
		transition:
			background 0.12s,
			color 0.12s;
	}
	.id-copy:hover {
		background: var(--ds-surface-2);
		color: var(--ds-text);
	}
	.ds-link {
		color: var(--ds-accent);
		word-break: break-all;
	}
	.ds-link:hover {
		text-decoration: underline;
	}
	:global(.exception-card) {
		border-color: var(--ds-danger);
	}
	/* process tab strip */
	.proc-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 1px;
		border-bottom: 1px solid var(--ds-border);
		margin-bottom: 16px;
	}
	.proc-tab {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 8px 14px;
		margin-bottom: -1px;
		border-bottom: 2px solid transparent;
		font-size: 13px;
		font-weight: 600;
		color: var(--ds-text-dim);
		transition:
			color 0.12s,
			border-color 0.12s;
	}
	.proc-tab:hover {
		color: var(--ds-text);
	}
	.proc-tab.active {
		color: var(--ds-accent-strong);
		border-bottom-color: var(--ds-accent);
	}
	.proc-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--ds-danger);
	}
</style>
