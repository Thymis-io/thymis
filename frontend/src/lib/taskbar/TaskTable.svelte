<script lang="ts">
	import { t } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { SvelteSet } from 'svelte/reactivity';
	import DataTable from '#lib/components/layout/DataTable.svelte';
	import RowActions from '#lib/components/layout/RowActions.svelte';
	import RowMenu, { type RowMenuItem } from '#lib/components/layout/RowMenu.svelte';
	import RenderTimeAgo from '#lib/components/RenderTimeAgo.svelte';
	import RenderTimeDuration from '#lib/components/RenderTimeDuration.svelte';
	import type { GlobalState } from '#lib/state.svelte.js';
	import { type TaskShort, cancelTask, retryTask } from '#lib/taskstatus.js';
	import {
		buildTaskTree,
		flattenSubtaskTree,
		flattenTaskTree,
		type TaskNode
	} from '#lib/taskTree.js';
	import TaskbarName from './TaskbarName.svelte';
	import TaskbarStatus from './TaskbarStatus.svelte';
	import TaskTreeIndent from './TaskTreeIndent.svelte';
	import TaskTreeMore from './TaskTreeMore.svelte';
	import Eye from 'lucide-svelte/icons/eye';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import Ban from 'lucide-svelte/icons/ban';

	interface Props {
		tasks: TaskShort[];
		globalState: GlobalState;
		/** Applies to top-level tasks; subtasks follow their root. */
		filter?: (root: TaskNode) => boolean;
		/** Show `tasks` as the subtasks of `parent`, its children at the top level. */
		parent?: TaskShort;
	}

	let { tasks, globalState, filter, parent }: Props = $props();

	const columnCount = 6;

	const expanded = new SvelteSet<string>();

	let rows = $derived.by(() => {
		if (parent) return flattenSubtaskTree(parent, tasks, expanded);
		const roots = buildTaskTree(tasks);
		return flattenTaskTree(filter ? roots.filter(filter) : roots, expanded);
	});

	const toggle = (parentId: string) => {
		if (!expanded.delete(parentId)) expanded.add(parentId);
	};

	const taskActions = (task: TaskShort): RowMenuItem[] => {
		const items: RowMenuItem[] = [
			{ label: $t('taskbar.details'), icon: Eye, href: `/tasks/${task.id}${page.url.search}` }
		];
		if (task.state === 'pending' || task.state === 'running') {
			items.push({
				label: $t('taskbar.cancel'),
				icon: Ban,
				variant: 'danger',
				onclick: () => cancelTask(task.id)
			});
		} else if (task.state === 'completed' || task.state === 'failed') {
			items.push({
				label: $t('taskbar.retry'),
				icon: RotateCcw,
				onclick: () => retryTask(task.id)
			});
		}
		return items;
	};

	// Make the task name navigate to its details page. The name can contain its
	// own device/config links, so ignore clicks that land on an inner anchor.
	const openTask = (event: MouseEvent, id: string) => {
		if ((event.target as HTMLElement).closest('a')) return;
		goto(`/tasks/${id}`);
	};
</script>

<DataTable
	columns={[
		{ label: $t('taskbar.task-type') },
		{ label: $t('taskbar.status') },
		{ label: $t('task-details.submitted') },
		{ label: $t('taskbar.start-time') },
		{ label: $t('taskbar.duration') },
		{ label: $t('taskbar.actions'), align: 'right' }
	]}
	{rows}
	empty={$t('taskbar.empty')}
>
	{#snippet row(item)}
		{#if item.kind === 'more'}
			<td colspan={columnCount}>
				<TaskTreeMore
					depth={item.depth}
					hidden={item.hidden}
					expanded={item.expanded}
					ontoggle={() => toggle(item.parentId)}
				/>
			</td>
		{:else}
			{@const task = item.task}
			<td>
				<TaskTreeIndent depth={item.depth}>
					<div
						class="task-name w-fit"
						role="link"
						tabindex="0"
						onclick={(e) => openTask(e, task.id)}
						onkeydown={(e) => {
							if (e.key === 'Enter') goto(`/tasks/${task.id}`);
						}}
					>
						<TaskbarName {globalState} {task} />
					</div>
				</TaskTreeIndent>
			</td>
			<td><TaskbarStatus {task} showProgress={false} /></td>
			<td>
				<RenderTimeAgo class="block" timestamp={task.submitted_time} minSeconds={1} />
			</td>
			<td>
				<RenderTimeAgo class="block" timestamp={task.start_time} minSeconds={1} />
			</td>
			<td>
				<RenderTimeDuration class="block" start={task.start_time} end={task.end_time} />
			</td>
			<td>
				<RowActions>
					<RowMenu label={$t('taskbar.actions')} items={taskActions(task)} />
				</RowActions>
			</td>
		{/if}
	{/snippet}
</DataTable>

<style lang="postcss">
	.task-name {
		cursor: pointer;
	}
	.task-name:hover {
		text-decoration: underline;
	}
</style>
