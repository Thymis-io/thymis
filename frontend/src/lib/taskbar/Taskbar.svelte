<script lang="ts">
	import { t } from 'svelte-i18n';
	import ResizableColumns from 'svelte-resizable-columns/src/ResizableColumns';
	import 'svelte-resizable-columns/src/resizableColumns.css';
	import { SvelteSet } from 'svelte/reactivity';
	import { taskStatus } from '#lib/taskstatus.js';
	import { buildTaskTree, flattenTaskTree } from '#lib/taskTree.js';
	import TaskbarActions from './TaskbarActions.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import TaskbarMinimize from './TaskbarMinimize.svelte';
	import TaskbarName from './TaskbarName.svelte';
	import TaskTreeIndent from './TaskTreeIndent.svelte';
	import TaskTreeMore from './TaskTreeMore.svelte';
	import RenderTimeAgo from '#lib/components/RenderTimeAgo.svelte';
	import RenderTimeDuration from '#lib/components/RenderTimeDuration.svelte';
	import type { GlobalState } from '#lib/state.svelte.js';

	interface Props {
		globalState: GlobalState;
		taskbarMinimized: boolean;
	}

	let { globalState, taskbarMinimized = $bindable() }: Props = $props();

	// The taskbar only ever shows the most recent tasks; the live store can grow
	// past that via websocket updates, so cap the rendered list here.
	const taskbarTaskLimit = 20;
	const expanded = new SvelteSet<string>();
	let rows = $derived(
		flattenTaskTree(buildTaskTree(Object.values($taskStatus)).slice(0, taskbarTaskLimit), expanded)
	);

	const toggle = (parentId: string) => {
		if (!expanded.delete(parentId)) expanded.add(parentId);
	};

	let headers = $derived([
		{ name: $t('taskbar.task-type') },
		{ name: $t('taskbar.status') },
		{ name: $t('taskbar.start-time'), additionalStyle: 'width: 16em' },
		{ name: $t('taskbar.duration'), additionalStyle: 'width: 16em' },
		{ name: $t('taskbar.actions'), additionalStyle: 'width: 10em' }
	]);

	const tdClass = 'px-3 py-1.5';
</script>

<!-- no overflow here: the #taskbar wrapper is the single vertical scroller, so the
     sticky header sticks correctly and we avoid a second (and a phantom horizontal)
     scrollbar. -->
<div class="ds-taskbar-table">
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
			{#each rows as row (row.kind === 'task' ? row.task.id : `more-${row.parentId}`)}
				<tr>
					{#if row.kind === 'more'}
						<td class={tdClass} colspan={headers.length}>
							<TaskTreeMore
								depth={row.depth}
								hidden={row.hidden}
								expanded={row.expanded}
								ontoggle={() => toggle(row.parentId)}
							/>
						</td>
					{:else}
						{@const task = row.task}
						<td class={tdClass}>
							<TaskTreeIndent depth={row.depth}>
								<TaskbarName {globalState} {task} />
							</TaskTreeIndent>
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
					{/if}
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
