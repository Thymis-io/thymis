<script lang="ts">
	import type { PageData } from './$types';
	import { t } from 'svelte-i18n';
	import { page } from '$app/stores';
	import { tasksByIdStore } from '$lib/taskstatus';
	import { Button } from 'flowbite-svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';

	export let data: PageData;

	$: task = $tasksByIdStore[$page.params.id] || data.task;

	// if task is undefined, go to 404
	const cleanStdOut = (stdoutorerr: string) => {
		const toRemove = '\r\u001b[K';
		return stdoutorerr.replaceAll(toRemove, '');
	};

	// if task is a command, build it by cat-ting data.program, data.args and data.env
	let command: string | undefined = undefined;
	$: {
		if (task && (task.type === 'commandtask' || task.type === 'nixcommandtask')) {
			let args = [];
			// for (let arg of task.data.args) {
			for (let arg of task.data.args as string[]) {
				if (arg.includes(' ')) {
					args.push(`"${arg}"`);
				} else {
					args.push(arg);
				}
			}
			command = task.data.program + ' ' + args.join(' ');
			if (task.data.env) {
				command =
					Object.entries(task.data.env)
						.map(([key, value]) => `${key}="${value}"`)
						.join(' ') +
					' ' +
					command;
			}
		}
	}

	// <!-- logs_by_level={
	// 	0: self.error_logs,
	// 	1: self.warnings,
	// 	2: self.notices,
	// 	3: self.infos, -->
	$: log_level_names = [$t('error'), $t('warning'), $t('notice'), $t('info')];
</script>

<h1 class="text-2xl font-bold">Task Detail for Task {task.id}: {task.display_name}</h1>

<h2 class="text-xl font-bold">Task State: {task.state}</h2>

{#if task.state === 'failed'}
	<h2 class="text-xl font-bold">Exception: {task.exception}</h2>
{/if}

<h2 class="text-xl font-bold">Start Time: <RenderUnixTimestamp timestamp={task.start_time} /></h2>

{#if task.end_time}
	<h2 class="text-xl font-bold">End Time: <RenderUnixTimestamp timestamp={task.end_time} /></h2>
{/if}

<h2 class="text-xl font-bold truncate">Detail: {JSON.stringify(task.data)}</h2>

{#if task.type === 'nixcommandtask'}
	<h2 class="text-xl font-bold">Nix Process Status:</h2>
	<ul>
		<li>Done: {task.status.done}</li>
		<li>Expected: {task.status.expected}</li>
		<li>Running: {task.status.running}</li>
		<li>Failed: {task.status.failed}</li>
		<ul>
			Errors:
			{#each task.status.errors as error}
				<MonospaceText code={error.msg}></MonospaceText>
			{/each}
		</ul>
		<!-- <li>Logs by Level: {JSON.stringify(task.status.logs_by_level)}</li> -->
	</ul>
	<!-- logs_by_level={
		0: self.error_logs,
		1: self.warnings,
		2: self.notices,
		3: self.infos, -->
	<!-- logs by level: we show a monospace text for each level -->
	{#each log_level_names as level_name, idx}
		{#if task.status.logs_by_level[idx].length > 0}
			<h2 class="text-xl font-bold">{level_name} Logs:</h2>
			{@const logs = task.status.logs_by_level[idx].join('\n')}
			<MonospaceText code={logs} />
		{:else}
			<h2 class="text-xl font-bold">No {level_name} Logs</h2>
		{/if}
	{/each}
{/if}

{#if task.type === 'commandtask' || task.type === 'nixcommandtask'}
	<h2 class="text-xl font-bold">Command:</h2>
	<MonospaceText code={command} />
	<h2 class="text-xl font-bold">Stdout:</h2>
	<MonospaceText code={cleanStdOut(task.stdout)} />
	<h2 class="text-xl font-bold">Stderr:</h2>
	<MonospaceText code={cleanStdOut(task.stderr)} />
{/if}

{#if task.type === 'compositetask'}
	<!-- We give links to the subtasks -->
	<h2 class="text-xl font-bold">Subtasks:</h2>
	<ul>
		{#each task.tasks as subtask, idx}
			<li>
				<span>Subtask {idx}: {subtask.display_name}</span>
				<a href="/tasks/{subtask.id}"
					><Button class="btn btn-sm btn-primary m-1">View Subtask {idx}</Button></a
				>
			</li>
		{/each}
	</ul>
{/if}
