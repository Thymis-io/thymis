<script lang="ts">
	import { Table, TableBody, TableBodyCell, TableBodyRow, TableHead } from 'flowbite-svelte';
	import { createSvelteTable, flexRender } from '@tanstack/svelte-table';
	import type { Task } from '$lib/taskstatus';
	import { onMount } from 'svelte';

	export let table: ReturnType<typeof createSvelteTable<Task>>;

	let columnSizing = $table.getState().columnSizing;
	let columnSizingInfo = $table.getState().columnSizingInfo;

	onMount(() => {
		const tableOptions = $table.options;
		const oldOnColumnSizingChange = $table.options.onColumnSizingChange;
		const oldOnColumnSizingInfoChange = $table.options.onColumnSizingInfoChange;
		if (!oldOnColumnSizingChange) {
			console.error('oldOnColumnSizingChange is not defined');
			return;
		}
		if (!oldOnColumnSizingInfoChange) {
			console.error('oldOnColumnSizingInfoChange is not defined');
			return;
		}
		// console.log('$table:', $table);
		tableOptions.onColumnSizingChange = (update) => {
			oldOnColumnSizingChange(update);
			columnSizing = $table.getState().columnSizing;
		};
		tableOptions.onColumnSizingInfoChange = (update) => {
			oldOnColumnSizingInfoChange(update);
			columnSizingInfo = $table.getState().columnSizingInfo;
		};
	});

	// $: sizingStyleString = Object.entries(columnSizing).map(([key, value]) => `--h
	let sizingStyleString = '';
	$: {
		// console.log(columnSizing, columnSizingInfo);
		const headers = $table.getFlatHeaders();
		const colSizes: { [key: string]: number } = {};
		for (const header of headers) {
			colSizes[`--header-${header.id}-width`] = header.getSize();
			colSizes[`--col-${header.column.id}-width`] = header.column.getSize();
		}
		sizingStyleString = Object.entries(colSizes)
			.map(([key, value]) => `${key}: ${value};`)
			.join(' ');
	}

	// $: console.log(columnSizing, columnSizingInfo);

	let clazz = '';
	export { clazz as class };
</script>

{#if $$slots.header}
	<div
		class="flex flex-col md:flex-row space-y-2 md:space-y-0 items-stretch md:items-center justify-end md:space-x-3 flex-shrink-0"
	>
		<slot name="header" />
	</div>
{/if}

<div style={sizingStyleString} class={clazz}>
	<Table class="table-fixed" divClass="max-h-full relative overflow-x-auto overflow-y-auto">
		<TableHead class="border-2 dark:border-0 sticky top-0">
			{#each $table.getHeaderGroups() as headerGroup}
				{#each headerGroup.headers as header}
					<th class="text-xs normal-case" style="width: calc(var(--header-{header.id}-width)*1px)">
						<div class="flex items-center justify-between">
							<div class="px-2">
								{#if !header.isPlaceholder}
									<svelte:component
										this={flexRender(header.column.columnDef.header, header.getContext())}
									/>
								{/if}
							</div>
							<div
								on:dblclick={() => header.column.resetSize()}
								on:mousedown={header.getResizeHandler()}
								on:touchstart={() => header.getResizeHandler()}
								class="resizer {$table.options.columnResizeDirection} {header.column.getIsResizing()
									? 'isResizing'
									: ''}"
							/>
						</div>
					</th>
				{/each}
			{/each}
		</TableHead>
		<TableBody tableBodyClass="">
			{#each $table.getRowModel().rows as row}
				<TableBodyRow>
					{#each row.getVisibleCells() as cell}
						<TableBodyCell
							class="overflow-x-clip px-2 py-2"
							style="width: calc(var(--col-{cell.column.id}-width)*1px)"
						>
							<div class="truncate">
								<svelte:component
									this={flexRender(cell.column.columnDef.cell, cell.getContext())}
								/>
							</div>
						</TableBodyCell>
					{/each}
				</TableBodyRow>
			{/each}
		</TableBody>
	</Table>
</div>

<style>
	.resizer {
		position: sticky;
		top: 0;
		height: 100%;
		min-height: 20px;
		right: 0;
		width: 5px;
		background: rgba(0, 0, 0, 0.5);
		cursor: col-resize;
		user-select: none;
		touch-action: none;
		z-index: 1000;
	}
	.resizer.isResizing {
		background: blue;
		opacity: 1;
	}

	@media (hover: hover) {
		.resizer {
			opacity: 0;
		}

		*:hover > .resizer {
			opacity: 1;
		}
	}
</style>
