<script lang="ts">
	import { t } from 'svelte-i18n';
	import ResizableColumns from 'svelte-resizable-columns/src/ResizableColumns';
	import 'svelte-resizable-columns/src/resizableColumns.css';
	import { taskStatus } from '$lib/taskstatus';
	import TaskbarActions from './TaskbarActions.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import TaskbarMinimize from './TaskbarMinimize.svelte';
	import TaskbarName from './TaskbarName.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import RenderTimeDuration from '$lib/components/RenderTimeDuration.svelte';

	export let taskbarMinimized: boolean;

	$: taskList = Object.values($taskStatus).sort((a, b) => (a.start_time < b.start_time ? 1 : -1));

	$: headers = [
		{ name: $t('taskbar.task-type') },
		{ name: $t('taskbar.status') },
		{ name: $t('taskbar.start-time'), additionalStyle: 'width: 16em' },
		{ name: $t('taskbar.duration'), additionalStyle: 'width: 16em' },
		{ name: $t('taskbar.actions'), additionalStyle: 'width: 10em' }
	];

	const tdClass = 'border border-gray-300 dark:border-gray-700 px-2';
</script>

<table class="w-full border-collapse" use:ResizableColumns>
	<thead>
		<tr class="sticky top-0 bg-gray-100 dark:bg-gray-800">
			{#each headers.entries() as [i, header]}
				<th
					class="border border-l-2 border-r-2 border-t-0 border-gray-300 dark:border-gray-600 text-base"
					style={header.additionalStyle}
				>
					{#if i === headers.length - 1}
						<TaskbarMinimize bind:taskbarMinimized />
					{/if}
					{header.name}
				</th>
			{/each}
		</tr>
	</thead>
	<tbody>
		{#each taskList as task}
			<tr>
				<td class={tdClass}>
					<TaskbarName {task} />
				</td>
				<td class={tdClass}>
					<TaskbarStatus {task} />
				</td>
				<td class={tdClass}>
					<RenderTimeAgo timestamp={task.start_time} minSeconds={1} />
				</td>
				<td class={tdClass}>
					<RenderTimeDuration start={task.start_time} end={task.end_time} />
				</td>
				<td class={tdClass}>
					<TaskbarActions {task} />
				</td>
			</tr>
		{/each}
	</tbody>
</table>

<style>
	th:first-child,
	td:first-child {
		border-left: none;
	}
	th:last-child,
	td:last-child {
		border-right: none;
	}
</style>
