<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';
	import { dndzone, type DndEvent } from 'svelte-dnd-action';
	import { flip } from 'svelte/animate';

	type DndItem = { id: string | number };
	type DndHandler = (e: CustomEvent<DndEvent<DndItem>>) => void;

	type Column = {
		/** Header label. Omit for spacer columns (e.g. a drag handle). */
		label?: string;
		align?: 'left' | 'right' | 'center';
		/** Extra classes for the <th> (e.g. a fixed width like `w-12`). */
		class?: string;
	};

	/** Drag-and-drop reordering config. Rows must expose a stable key via `rowKey`. */
	type Dnd = {
		dragDisabled: boolean;
		flipDurationMs: number;
		onConsider: (e: CustomEvent<DndEvent<T>>) => void;
		onFinalize: (e: CustomEvent<DndEvent<T>>) => void;
	};

	interface Props {
		columns: Column[];
		rows: T[];
		/** Empty-state text shown when `rows` is empty. */
		empty?: string;
		/** Renders the cells (<td>…</td>) for one row. */
		row: Snippet<[T, number]>;
		class?: string;
		/** Enable drag-and-drop row reordering. Requires `rowKey`. */
		dnd?: Dnd;
		/** Stable key for each row; used for keyed iteration and flip animations. */
		rowKey?: (item: T, index: number) => string | number;
	}

	let { columns, rows, empty, row, class: className = '', dnd, rowKey }: Props = $props();

	const alignClass = (a?: Column['align']) =>
		a === 'right' ? 'text-right' : a === 'center' ? 'text-center' : '';

	const key = (item: T, i: number) => (rowKey ? rowKey(item, i) : i);

	let tableEl = $state<HTMLTableElement>();

	const transformDraggedElement = (draggedEl?: HTMLElement) => {
		if (!draggedEl) return;
		draggedEl.style.display = 'table';
		draggedEl.style.tableLayout = 'fixed';
		draggedEl.style.opacity = '1';
		draggedEl.style.background = 'var(--ds-surface-2)';
		draggedEl.style.boxShadow = 'var(--ds-shadow-lg)';
		draggedEl.style.borderRadius = 'var(--ds-radius)';
		const headerCells = tableEl?.querySelectorAll('thead th');
		if (!headerCells) return;
		draggedEl.querySelectorAll(':scope > td').forEach((td, i) => {
			const th = headerCells[i] as HTMLElement | undefined;
			const cell = td as HTMLElement;
			if (th) {
				cell.style.width = `${th.getBoundingClientRect().width}px`;
				cell.style.padding = getComputedStyle(th).padding;
				cell.style.boxSizing = 'border-box';
			}
		});
	};
</script>

<div class="ds-table-wrap {className}" data-testid="data-table">
	<table class="ds-table" bind:this={tableEl}>
		<thead>
			<tr>
				{#each columns as col}
					<th class="{alignClass(col.align)} {col.class ?? ''}">{col.label ?? ''}</th>
				{/each}
			</tr>
		</thead>
		{#if dnd}
			<!-- svelte-dnd-action's Item type requires an `id`; the generic T can't express
			     that, and callers enabling `dnd` pass rows that carry one. Cast to bridge it. -->
			<tbody
				use:dndzone={{
					items: rows as DndItem[],
					dragDisabled: dnd.dragDisabled,
					flipDurationMs: dnd.flipDurationMs,
					transformDraggedElement,
					dropTargetStyle: {}
				}}
				onconsider={dnd.onConsider as DndHandler}
				onfinalize={dnd.onFinalize as DndHandler}
			>
				{#each rows as item, i (key(item, i))}
					<tr animate:flip={{ duration: dnd.flipDurationMs }}>
						{@render row(item, i)}
					</tr>
				{:else}
					{#if empty}
						<tr>
							<td colspan={columns.length} class="ds-table-empty">{empty}</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		{:else}
			<tbody>
				{#each rows as item, i}
					<tr>
						{@render row(item, i)}
					</tr>
				{:else}
					{#if empty}
						<tr>
							<td colspan={columns.length} class="ds-table-empty">{empty}</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		{/if}
	</table>
</div>
