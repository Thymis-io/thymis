<script lang="ts">
	import type { PageData } from './$types';
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { Button } from 'flowbite-svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';

	export let data: PageData;

	$: task = data.task;

	// 	export type TaskState = 'pending' | 'running' | 'completed' | 'failed';

	// export type Task = {
	// 	id: string;
	// 	start_time: string;
	// 	end_time?: string;
	// 	state: TaskState;
	// 	exception?: string;
	// 	task_type: string;
	// 	task_submission_data: Record<string, unknown>;

	// 	parent_task_id?: string;
	// 	children?: string[];

	// 	process_program?: string;
	// 	process_args?: string[];
	// 	process_env?: Record<string, string>;
	// 	process_stdout?: string;
	// 	process_stderr?: string;

	// 	nix_status?: {
	// 		done: number;
	// 		expected: number;
	// 		running: number;
	// 		failed: number;
	// 		errors: unknown[];
	// 		logs_by_level: Record<number, string[]>;
	// 	};
	// 	nix_files_linked?: number;
	// 	nix_bytes_linked?: number;
	// 	nix_corrupted_paths?: number;
	// 	nix_untrusted_paths?: number;
	// 	nix_errors?: Record<string, unknown>;
	// 	nix_warnings?: Record<string, unknown>;
	// 	nix_notices?: Record<string, unknown>;
	// 	nix_infos?: Record<string, unknown>;
	// };

	// if task is undefined, go to 404
	const cleanStdOut = (stdoutorerr: string) => {
		const toRemove = '\r\u001b[K';
		return stdoutorerr.replaceAll(toRemove, '');
	};

	// <!-- logs_by_level={
	// 	0: self.error_logs,
	// 	1: self.warnings,
	// 	2: self.notices,
	// 	3: self.infos, -->
	$: log_level_names = [$t('error'), $t('warning'), $t('notice'), $t('info')];

	const escapeForDoubleQuotes = (str: string) => {
		// quote ", `, \ and $
		return str.replaceAll(/["`\\$]/g, '\\$&');
	};
</script>

{#if task}
	<h1>Task type={task.task_type}, id={task.id}</h1>

	<p>Current status: {task.state}</p>

	{#if task.state === 'pending'}
		<p>Task is pending</p>
	{:else if task.state === 'running'}
		<p>Task is running</p>
	{:else if task.state === 'completed'}
		<p>Task is completed</p>
	{:else if task.state === 'failed'}
		<p>Task has failed</p>
	{/if}

	{#if task.exception}
		<p>Exception: {task.exception}</p>
	{/if}

	<div>
		<h2>Task times</h2>
		<p>Start time: <RenderUnixTimestamp timestamp={task.start_time} /></p>
		{#if task.end_time}
			<p>End time: <RenderUnixTimestamp timestamp={task.end_time} /></p>
		{:else}
			<p>Task is still running, no end time</p>
		{/if}
	</div>

	<hr />

	<div>
		<h2>Task submission data</h2>
		<MonospaceText code={JSON.stringify(task.task_submission_data, null, 2)} />
	</div>

	<hr />

	<div>
		<h2>Parent and children</h2>
		{#if task.parent_task_id}
			<p>Parent task: {task.parent_task_id}</p>
		{:else}
			<p>No parent task</p>
		{/if}

		{#if task.children && task.children.length > 0}
			<p>Children tasks: {task.children.join(', ')}</p>
		{:else}
			<p>No children tasks</p>
		{/if}
	</div>

	<hr />

	<div>
		<h2>Process</h2>
		{#if task.process_program && task.process_args && task.process_env}
			<MonospaceText
				code={Object.entries(task.process_env)
					.map(([key, value]) => `${key}="${escapeForDoubleQuotes(value)}"`)
					.join(' ') +
					' ' +
					task.process_program +
					' ' +
					task.process_args
						.map((arg) =>
							`"${escapeForDoubleQuotes(arg)}"` ? escapeForDoubleQuotes(arg) !== arg : arg
						)
						.join(' ')}
			/>
		{:else}
			<p>No process information</p>
		{/if}

		{#if task.nix_status?.errors && task.nix_status.errors.length > 0}
			<p>Nix errors:</p>
			<MonospaceText code={task.nix_status.errors.map((error) => error.msg).join('\n')} />
		{/if}

		{#if task.nix_errors && task.nix_errors.length > 0}
			<p>Nix errors:</p>
			<MonospaceText code={task.nix_errors.join('\n')} />
		{/if}

		{#if task.nix_warnings && task.nix_warnings.length > 0}
			<p>Nix warnings:</p>
			<MonospaceText code={task.nix_warnings.join('\n')} />
		{/if}

		{#if task.nix_notices && task.nix_notices.length > 0}
			<p>Nix notices:</p>
			<MonospaceText code={task.nix_notices.join('\n')} />
		{/if}

		{#if task.nix_infos && task.nix_infos.length > 0}
			<p>Nix infos:</p>
			<MonospaceText code={task.nix_infos.join('\n')} />
		{/if}

		{#if task.process_stdout}
			<p>Standard output:</p>
			<MonospaceText code={cleanStdOut(task.process_stdout)} />
		{:else}
			<p>No standard output</p>
		{/if}

		{#if task.process_stderr}
			<p>Standard error:</p>
			<MonospaceText code={cleanStdOut(task.process_stderr)} />
		{:else}
			<p>No standard error</p>
		{/if}
	</div>

	<hr />
{/if}
