<script lang="ts">
	import {
		globalNavSelectedDevice,
		globalNavSelectedTarget,
		globalNavSelectedTargetType,
		state,
		type ModuleSettings
	} from '$lib/state';
	import { taskStatus, type Task } from '$lib/taskstatus';
	import {
		Table,
		TableBody,
		TableBodyCell,
		TableBodyRow,
		TableHead,
		TableHeadCell
	} from 'flowbite-svelte';

	import DataTable from './DataTable.svelte';
	import {
		createSvelteTable,
		flexRender,
		getCoreRowModel,
		createColumnHelper,
		getSortedRowModel
	} from '@tanstack/svelte-table';
	import type {
		ColumnDef,
		TableOptions,
		ColumnSizingState,
		ColumnSizingInfoState
	} from '@tanstack/svelte-table';
	import { t } from 'svelte-i18n';

	import TaskbarActions from './TaskbarActions.svelte';
	import { derived, writable } from 'svelte/store';

	// columns:
	// - start time
	// - end time *if available*
	// - task name (what type of task it is)
	// - status (pending, running with progress bar, completed, failed)
	// - detail (custom string for what the task does)
	// - exception (if failed, custom string for what went wrong)
	// - user (who started the task)
	// - action buttons
	//     - cancel: kills or dequeues the task
	//     - retry: requeues the task
	//     - view: opens a site-specific view of the task

	// const columns = table.createColumns([
	// 	table.column({
	// 		header: 'Start Time',
	// 		// accessor: (task) => task.start_time,
	// 		accessor: 'start_time',
	// 		cell: (item) => item.value,
	//         plugins: {
	//             resize: {
	//                 initialWidth: 100,
	//                 disable: true
	//             }
	//         }
	// 	}),
	// 	table.column({
	// 		header: 'End Time',
	// 		// accessor: (task) => task.end_time,
	// 		accessor: (task) => 'Not implemented',
	// 		cell: (item) => item.value
	// 	}),
	// 	table.column({
	// 		header: 'Task',
	// 		// accessor: (task) => task.display_name,
	// 		accessor: 'display_name',
	// 		cell: (item) => item.value
	// 	}),
	// 	table.column({
	// 		header: 'Status',
	// 		// accessor: (task) => task.state,
	// 		accessor: 'state',
	// 		cell: (item) => item.value
	// 	}),
	// 	table.column({
	// 		header: 'Detail',
	// 		accessor: (task) => JSON.stringify(task.data),
	// 		cell: (item) => item.value
	// 	}),
	// 	table.column({
	// 		header: 'Exception',
	// 		accessor: (task) => task.exception,
	// 		cell: (item) => item.value || 'No exception'
	// 	}),
	// 	table.column({
	// 		header: 'User',
	// 		accessor: (task) => 'Not implemented',
	// 		cell: (item) => item.value
	// 	}),
	// 	table.column({
	// 		header: 'Actions',
	// 		// accessor: (task) => "Not implemented",
	// 		accessor: (task) => task,
	// 		cell: (item) =>
	// 			createRender(TaskbarActions, {
	// 				task: item.value
	// 			})
	// 	})
	// ]);

	const coreRowModel = getCoreRowModel();
	const sortedRowModel = getSortedRowModel();
	const columnHelper = createColumnHelper<Task>();

	const tableOptions = derived([taskStatus], ([taskStatusValue]) => {
		return {
			data: taskStatusValue,
			columns: [
				columnHelper.accessor('start_time', {
					cell: (item) => item.getValue(),
					header: 'Start Time',
					size: 150
				}),
				columnHelper.display({
					cell: (item) => 'Not implemented',
					header: 'End Time',
					id: 'end_time',
					size: 150
				}),
				columnHelper.accessor('display_name', {
					cell: (item) => item.getValue(),
					header: 'Task',
					size: 1200
				}),
				columnHelper.accessor('state', {
					cell: (item) => item.getValue(),
					header: 'Status',
					size: 150
				}),
				columnHelper.accessor('data', {
					cell: (item) => JSON.stringify(item.getValue()),
					header: 'Detail',
					size: 150
				}),
				columnHelper.accessor('exception', {
					cell: (item) => item.getValue() || 'No exception',
					header: 'Exception',
					size: 100
				}),
				columnHelper.display({
					cell: (item) => 'Not implemented',
					header: 'User',
					id: 'user',
					size: 100
				}),
				columnHelper.accessor((task) => task, {
					cell: (item) =>
						flexRender(TaskbarActions, {
							task: item.getValue(),
							taskIdx: item.row.index
						}),
					header: 'Actions',
					size: 300
				})
			],
			defaultColumn: {
				minSize: 30,
				size: 1000,
				maxSize: 2000
			},
			columnResizeMode: 'onChange',
			getCoreRowModel: coreRowModel,
			getSortedRowModel: sortedRowModel,
			initialState: {
				sorting: [
					{
						id: 'start_time',
						desc: true // sort by name in descending order by default
					}
				]
			}
		} satisfies Parameters<typeof createSvelteTable<Task>>[0];
	});

	const table = createSvelteTable(tableOptions);
</script>

{#if $taskStatus}
	<DataTable class="max-h-full flex" {table} />
{/if}
