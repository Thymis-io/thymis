<script lang="ts" generics="T">
	import type { Snippet } from 'svelte';

	type Column = {
		/** Header label. Omit for spacer columns (e.g. a drag handle). */
		label?: string;
		align?: 'left' | 'right' | 'center';
		/** Extra classes for the <th> (e.g. a fixed width like `w-12`). */
		class?: string;
	};

	interface Props {
		columns: Column[];
		rows: T[];
		/** Empty-state text shown when `rows` is empty. */
		empty?: string;
		/** Renders the cells (<td>…</td>) for one row. */
		row: Snippet<[T, number]>;
		class?: string;
	}

	let { columns, rows, empty, row, class: className = '' }: Props = $props();

	const alignClass = (a?: Column['align']) =>
		a === 'right' ? 'text-right' : a === 'center' ? 'text-center' : '';
</script>

<div class="ds-table-wrap {className}">
	<table class="ds-table">
		<thead>
			<tr>
				{#each columns as col}
					<th class="{alignClass(col.align)} {col.class ?? ''}">{col.label ?? ''}</th>
				{/each}
			</tr>
		</thead>
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
	</table>
</div>
