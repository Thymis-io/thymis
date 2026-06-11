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
	import type { GlobalState } from '$lib/state.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';

	interface Props {
		globalState: GlobalState;
		deploymentInfos: DeploymentInfo[];
		taskbarMinimized: boolean;
	}

	let { globalState, deploymentInfos, taskbarMinimized = $bindable() }: Props = $props();

	let taskList = $derived(
		Object.values($taskStatus).sort((a, b) => (a.start_time < b.start_time ? 1 : -1))
	);

	let headers = $derived([
		{ name: $t('taskbar.task-type') },
		{ name: $t('taskbar.status') },
		{ name: $t('taskbar.start-time'), additionalStyle: 'width: 16em' },
		{ name: $t('taskbar.duration'), additionalStyle: 'width: 16em' },
		{ name: $t('taskbar.actions'), additionalStyle: 'width: 10em' }
	]);

	const tdClass = 'px-3 py-1.5';
</script>

<div class="ds-taskbar-table overflow-y-auto">
	<table class="w-full border-collapse" use:ResizableColumns>
		<thead>
			<tr class="sticky top-0">
				{#each headers.entries() as [i, header]}
					<th style={header.additionalStyle}>
						{#if i === headers.length - 1}
							<TaskbarMinimize bind:taskbarMinimized />
						{/if}
						{header.name}
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each taskList as task (task.id)}
				<tr>
					<td class={tdClass}>
						<TaskbarName {globalState} {deploymentInfos} {task} />
					</td>
					<td class={tdClass}>
						<TaskbarStatus {task} />
					</td>
					<td class={tdClass}>
						<RenderTimeAgo class="block" timestamp={task.start_time} minSeconds={1} />
					</td>
					<td class={tdClass}>
						<RenderTimeDuration class="block" start={task.start_time} end={task.end_time} />
					</td>
					<td class={tdClass}>
						<TaskbarActions {task} />
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style lang="postcss">
	.ds-taskbar-table table {
		font-size: 13px;
		color: var(--ds-text);
	}
	.ds-taskbar-table thead th {
		background: var(--ds-surface-2);
		color: var(--ds-text-mute);
		font-size: 11.5px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		text-align: left;
		padding: 9px 12px;
		border-bottom: 1px solid var(--ds-border);
		border-right: 1px solid var(--ds-border);
	}
	.ds-taskbar-table thead th:last-child {
		border-right: none;
	}
	.ds-taskbar-table tbody td {
		border-bottom: 1px solid var(--ds-border);
		vertical-align: middle;
	}
	.ds-taskbar-table tbody tr {
		transition: background 0.12s;
	}
	.ds-taskbar-table tbody tr:hover {
		background: var(--ds-surface-2);
	}
</style>
