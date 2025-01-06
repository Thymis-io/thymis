<script lang="ts">
	import { t } from 'svelte-i18n';
	import ResizableColumns from 'svelte-resizable-columns/src/ResizableColumns';
	import 'svelte-resizable-columns/src/resizableColumns.css';
	import { taskStatus, type Task, type TaskShort } from '$lib/taskstatus';

	import TaskbarActions from './TaskbarActions.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';

	$: taskList = Object.values($taskStatus).sort((a, b) => (a.start_time < b.start_time ? 1 : -1));

	const headers = [
		{ name: $t('taskbar.start-time') },
		{ name: $t('taskbar.end-time') },
		{ name: $t('taskbar.task-type') },
		{ name: $t('taskbar.status') },
		{ name: $t('taskbar.actions'), additionalStyle: 'width: 10%' }
	];

	const localizeTaskType = {
		build_project_task: $t('taskbar.task-types.build_project'),
		project_flake_update_task: $t('taskbar.task-types.project_flake_update')
	};
</script>

<table class="w-full border-collapse" use:ResizableColumns>
	<thead>
		<tr class="sticky top-0 bg-gray-100 dark:bg-gray-800">
			{#each headers as header}
				<th
					class="border border-l-2 border-r-2 border-gray-300 dark:border-gray-600"
					style={header.additionalStyle}
				>
					{header.name}
				</th>
			{/each}
		</tr>
	</thead>
	<tbody>
		{#each taskList as task}
			<tr>
				<td class="border border-gray-300 dark:border-gray-700">
					<RenderUnixTimestamp timestamp={task.start_time} />
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
					<RenderUnixTimestamp timestamp={task.end_time} />
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
					{task.task_type in localizeTaskType ? localizeTaskType[task.task_type] : task.task_type}
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
					<TaskbarStatus {task} />
				</td>
				<td class="border border-gray-300 dark:border-gray-700 flex justify-center">
					<TaskbarActions {task} />
				</td>
			</tr>
		{/each}
	</tbody>
</table>
