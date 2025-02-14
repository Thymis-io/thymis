<script lang="ts">
	import { t } from 'svelte-i18n';
	import ResizableColumns from 'svelte-resizable-columns/src/ResizableColumns';
	import 'svelte-resizable-columns/src/resizableColumns.css';
	import { taskStatus, type Task, type TaskShort } from '$lib/taskstatus';

	import TaskbarActions from './TaskbarActions.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';
	import TaskbarMinimize from './TaskbarMinimize.svelte';
	import { state } from '$lib/state';

	export let taskbarMinimized: boolean;

	$: taskList = Object.values($taskStatus).sort((a, b) => (a.start_time < b.start_time ? 1 : -1));

	const headers = [
		{ name: $t('taskbar.start-time') },
		{ name: $t('taskbar.end-time') },
		{ name: $t('taskbar.task-type') },
		{ name: $t('taskbar.status') },
		{ name: $t('taskbar.actions'), additionalStyle: 'width: 10%' }
	];

	const configToDisplayName = (identifier: string | undefined) => {
		if (!identifier) return '';
		const device = $state.configs.find((config) => config.identifier === identifier);
		return device ? device.displayName : identifier;
	};
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
				<td class="border border-gray-300 dark:border-gray-700">
					<RenderUnixTimestamp timestamp={task.start_time} />
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
					<RenderUnixTimestamp timestamp={task.end_time} />
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
					{#if task.task_type === 'project_flake_update_task'}
						{$t('taskbar.task-types.project_flake_update')}
					{:else if task.task_type === 'build_project_task'}
						{$t('taskbar.task-types.build_project')}
					{:else if task.task_type === 'deploy_devices_task'}
						{$t('taskbar.task-types.deploy_devices')}
					{:else if task.task_type === 'deploy_device_task'}
						{@const name = configToDisplayName(task.task_submission_data?.device?.identifier)}
						{$t('taskbar.task-types.deploy_device', { values: { device: name } })}
					{:else if task.task_type === 'build_device_image_task'}
						{@const name = configToDisplayName(task.task_submission_data?.configuration_id)}
						{$t('taskbar.task-types.build_device_image', { values: { device: name } })}
					{:else if task.task_type === 'ssh_command_task'}
						{$t('taskbar.task-types.ssh_command')}
					{:else if task.task_type === 'run_nixos_vm_task'}
						{@const name = configToDisplayName(task.task_submission_data?.configuration_id)}
						{$t('taskbar.task-types.run_nixos_vm_task', { values: { device: name } })}
					{:else}
						{task.task_type}
					{/if}
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
					<TaskbarStatus {task} />
				</td>
				<td class="border border-gray-300 dark:border-gray-700">
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
