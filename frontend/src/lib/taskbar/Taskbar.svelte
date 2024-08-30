<script lang="ts">
	import { taskStatus, type Task } from '$lib/taskstatus';

	import DataTable from './DataTable.svelte';
	import {
		createSvelteTable,
		flexRender,
		getCoreRowModel,
		createColumnHelper,
		getSortedRowModel
	} from '@tanstack/svelte-table';

	import TaskbarActions from './TaskbarActions.svelte';
	import { derived } from 'svelte/store';
	import RenderUnixTimestamp from '$lib/components/RenderUnixTimestamp.svelte';

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

	const coreRowModel = getCoreRowModel();
	const sortedRowModel = getSortedRowModel();
	const columnHelper = createColumnHelper<Task>();

	const tableOptions = derived([taskStatus], ([taskStatusValue]) => {
		return {
			data: taskStatusValue,
			columns: [
				columnHelper.accessor('start_time', {
					cell: (item) => flexRender(RenderUnixTimestamp, { timestamp: item.getValue() }),
					header: 'Start Time',
					size: 150
				}),
				columnHelper.accessor('end_time', {
					cell: (item) => flexRender(RenderUnixTimestamp, { timestamp: item.getValue() }),
					header: 'End Time',
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
				// columnHelper.display({
				// 	cell: (item) => 'Not implemented',
				// 	header: 'User',
				// 	id: 'user',
				// 	size: 100
				// }),
				columnHelper.accessor((task) => task, {
					cell: (item) =>
						flexRender(TaskbarActions, {
							task: item.getValue()
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
	<DataTable class="h-[calc(100%-40px)] flex" {table} />
{/if}
