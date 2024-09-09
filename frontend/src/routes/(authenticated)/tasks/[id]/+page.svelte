<script lang="ts">
	import type { PageData } from './$types';
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
		if (task && task.type === 'commandtask') {
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

<h2 class="text-xl font-bold">Detail: {JSON.stringify(task.data)}</h2>

{#if task.type === 'commandtask'}
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
