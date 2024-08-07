<script lang="ts">
	import type { PageData } from './$types';
	import { page } from '$app/stores';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import { Button } from 'flowbite-svelte';
	import MonospaceText from '$lib/components/MonospaceText.svelte';

	export let data: PageData;

	// $: taskIdx = $page.params.id;
	$: taskIdx = Number($page.params.id);
	$: task = $taskStatus[taskIdx];
	//     export type TaskState = 'pending' | 'running' | 'completed' | 'failed';
	// export type TaskVanilla = {
	// 	type: 'task';
	// 	display_name: string;
	// 	state: TaskState;
	// 	exception?: string;
	// 	start_time: number;
	// 	data: Record<string, any>;
	// };
	// export type CommandTask = Omit<TaskVanilla, 'type'> & {
	// 	type: 'commandtask';
	// 	stdout: string;
	// 	stderr: string;
	// };
	// export type CompositeTask = Omit<TaskVanilla, 'type'> & {
	// 	type: 'compositetask';
	// 	tasks: TaskList;
	// };

	// export type Task = TaskVanilla | CommandTask | CompositeTask;

	// if task is undefined, go to 404
	const cleanStdOut = (stdoutorerr: string) => {
		const toRemove = '\r\u001b[K';
		return stdoutorerr.replaceAll(toRemove, '');
	};
</script>

<h1 class="text-2xl font-bold">Task Detail for Task {taskIdx}: {task.display_name}</h1>

<h2 class="text-xl font-bold">Task State: {task.state}</h2>

{#if task.state === 'failed'}
	<h2 class="text-xl font-bold">Exception: {task.exception}</h2>
{/if}

<h2 class="text-xl font-bold">Start Time: {task.start_time}</h2>

<h2 class="text-xl font-bold">Detail: {JSON.stringify(task.data)}</h2>

{#if task.type === 'commandtask'}
	<!-- <h2 class="text-xl font-bold">Stdout: {task.stdout}</h2>
    <h2 class="text-xl font-bold">Stderr: {task.stderr}</h2> -->
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
				<a href="/tasks/{idx}"
					><Button class="btn btn-sm btn-primary m-1">View Subtask {idx}</Button></a
				>
			</li>
		{/each}
	</ul>
{/if}
