<script lang="ts">
	import type { PageData } from './$types';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';
	import { subscribedTask, subscribeTask, type Task } from '$lib/taskstatus';
	import PageHead from '$lib/components/layout/PageHead.svelte';
	import TaskbarName from '$lib/taskbar/TaskbarName.svelte';
	import TaskbarStatus from '$lib/taskbar/TaskbarStatus.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	let task: Task | undefined = $derived(!$subscribedTask ? data.task : $subscribedTask);

	// if task is undefined, go to 404
	const cleanStdOut = (stdoutorerr: string) => {
		const toRemove = '\r\u001b[K';
		return stdoutorerr.replaceAll(toRemove, '');
	};

	const escapeForDoubleQuotes = (str: string) => {
		// quote ", `, \ and $
		return str.replaceAll(/["`\\$]/g, '\\$&');
	};

	const needsDoubleQuotes = (str: string) => {
		return str !== escapeForDoubleQuotes(str) || str.includes(' ');
	};

	$effect(() => {
		subscribeTask(data.task_id);
	});
</script>

<PageHead repoStatus={data.repoStatus} globalState={data.globalState} nav={data.nav}>
	{#if task}
		<div class="text-3xl font-bold">
			<TaskbarName globalState={data.globalState} {task} iconSize={24} />
		</div>
	{/if}
</PageHead>

{#if task}
	<div class="flex flex-wrap items-center gap-4 mb-4">
		<TaskbarStatus {task} showProgress={false} />
		<h1>id: {task.id}</h1>

		<p>Start time: <RenderUnixTimestamp timestamp={task.start_time} /></p>
		{#if task.end_time}
			<p>End time: <RenderUnixTimestamp timestamp={task.end_time} /></p>
		{:else}
			<p>Task is still running, no end time</p>
		{/if}
	</div>

	{#if task.exception}
		<p>Exception:</p>
		<MonospaceText code={task.exception} />
	{/if}

	<div class="my-4">
		<h2>Task submission data</h2>
		<MonospaceText
			code={JSON.stringify(task.task_submission_data || task.task_submission_data_raw, null, 2)}
		/>
	</div>

	<hr />

	{#if task.parent_task_id || (task.children && task.children.length > 0)}
		<div class="my-4">
			{#if task.parent_task_id}
				<p>Parent task: {task.parent_task_id}</p>
			{/if}

			{#if task.children && task.children.length > 0}
				<p>Children tasks: {task.children.join(', ')}</p>
			{/if}
		</div>

		<hr />
	{/if}

	<div class="my-4">
		{#if task.processes && task.processes.length > 0}
			{#each task.processes as process, i (process.process_index)}
				<h3 class="mt-4">Process {i + 1}</h3>
				{#if process.process_program && process.process_args}
					<MonospaceText
						code={(process.process_env
							? Object.entries(process.process_env)
									.map(([key, value]) => `${key}="${escapeForDoubleQuotes(value)}"`)
									.join(' ') + ' '
							: '') +
							process.process_program +
							' ' +
							process.process_args
								.map((arg) => (needsDoubleQuotes(arg) ? `"${escapeForDoubleQuotes(arg)}"` : arg))
								.join(' ')}
					/>
				{:else}
					<p>No process information</p>
				{/if}

				{#if process.nix_errors && process.nix_errors.length > 0}
					<p>Nix errors:</p>
					<MonospaceText code={process.nix_errors.map((error) => error.msg).join('\n')} />
				{/if}

				{#if process.nix_error_logs && process.nix_error_logs.length > 0}
					<p>Nix error logs:</p>
					<MonospaceText code={process.nix_error_logs.join('\n')} />
				{/if}

				{#if process.nix_warning_logs && process.nix_warning_logs.length > 0}
					<p>Nix warnings:</p>
					<MonospaceText code={process.nix_warning_logs.join('\n')} />
				{/if}

				{#if process.nix_notice_logs && process.nix_notice_logs.length > 0}
					<p>Nix notices:</p>
					<MonospaceText code={process.nix_notice_logs.join('\n')} />
				{/if}

				{#if process.nix_info_logs && process.nix_info_logs.length > 0}
					<p>Nix infos:</p>
					<MonospaceText code={process.nix_info_logs.join('\n')} />
				{/if}

				{#if process.process_stdout}
					<p>Standard output:</p>
					<MonospaceText code={cleanStdOut(process.process_stdout)} />
				{:else}
					<p>No standard output</p>
				{/if}

				{#if process.process_stderr}
					<p>Standard error:</p>
					<MonospaceText code={cleanStdOut(process.process_stderr)} />
				{:else}
					<p>No standard error</p>
				{/if}

				{#if i < task.processes.length - 1}
					<hr class="mt-4" />
				{/if}
			{/each}
		{:else}
			<p>No processes</p>
		{/if}
	</div>

	<hr />
{/if}
