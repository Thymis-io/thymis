<script lang="ts" generics="T, K extends string | number = string | number">
	import type { Snippet } from 'svelte';
	import { t } from 'svelte-i18n';
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
		rowKey?: (item: T, index: number) => K;
		/** Render a leading checkbox column for row selection. Requires `rowKey`. */
		selectable?: boolean;
		/** Keys (from `rowKey`) of the selected rows. Bindable. */
		selected?: K[];
	}

	let {
		columns,
		rows,
		empty,
		row,
		class: className = '',
		dnd,
		rowKey,
		selectable = false,
		selected = $bindable([])
	}: Props = $props();

	const alignClass = (a?: Column['align']) =>
		a === 'right' ? 'text-right' : a === 'center' ? 'text-center' : '';

	// Without `rowKey` the index is the key (only valid for callers that don't set K).
	const key = (item: T, i: number): K => (rowKey ? rowKey(item, i) : (i as K));

	// Leading checkbox column (when selectable) shifts every other column by one.
	let colspan = $derived(columns.length + (selectable ? 1 : 0));

	let rowKeys = $derived(rows.map((item, i) => key(item, i)));
	let selectedSet = $derived(new Set(selected));
	let selectedVisibleCount = $derived(rowKeys.filter((k) => selectedSet.has(k)).length);
	let allSelected = $derived(rowKeys.length > 0 && selectedVisibleCount === rowKeys.length);
	let someSelected = $derived(selectedVisibleCount > 0 && !allSelected);

	let headerCheckbox = $state<HTMLInputElement>();
	$effect(() => {
		if (headerCheckbox) headerCheckbox.indeterminate = someSelected;
	});

	const toggleAll = () => {
		if (allSelected) {
			const visible = new Set(rowKeys);
			selected = selected.filter((k) => !visible.has(k));
		} else {
			selected = [...selected, ...rowKeys.filter((k) => !selectedSet.has(k))];
		}
	};

	const toggleRow = (k: K) => {
		selected = selectedSet.has(k) ? selected.filter((s) => s !== k) : [...selected, k];
	};

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

{#snippet selectCell(item: T, i: number)}
	{#if selectable}
		{@const k = key(item, i)}
		<td class="ds-table-select">
			<label>
				<input
					type="checkbox"
					class="ds-checkbox"
					aria-label={$t('common.select-row')}
					checked={selectedSet.has(k)}
					onchange={() => toggleRow(k)}
				/>
			</label>
		</td>
	{/if}
{/snippet}

<div class="ds-table-wrap {className}" data-testid="data-table">
	<table class="ds-table" bind:this={tableEl}>
		<thead>
			<tr>
				{#if selectable}
					<th class="ds-table-select">
						<label>
							<input
								bind:this={headerCheckbox}
								type="checkbox"
								class="ds-checkbox"
								aria-label={$t('common.select-all')}
								checked={allSelected}
								disabled={rowKeys.length === 0}
								onchange={toggleAll}
							/>
						</label>
					</th>
				{/if}
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
						{@render selectCell(item, i)}
						{@render row(item, i)}
					</tr>
				{:else}
					{#if empty}
						<tr>
							<td {colspan} class="ds-table-empty">{empty}</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		{:else}
			<tbody>
				{#each rows as item, i}
					<tr>
						{@render selectCell(item, i)}
						{@render row(item, i)}
					</tr>
				{:else}
					{#if empty}
						<tr>
							<td {colspan} class="ds-table-empty">{empty}</td>
						</tr>
					{/if}
				{/each}
			</tbody>
		{/if}
	</table>
</div>
