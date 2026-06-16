<script lang="ts">
	import { t } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { page as pageStore } from '$app/stores';
	import type { PageData } from './$types';
	import Page from '$lib/components/layout/Page.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import FilterChips from '$lib/components/layout/FilterChips.svelte';
	import RowActions from '$lib/components/layout/RowActions.svelte';
	import RowMenu, { type RowMenuItem } from '$lib/components/layout/RowMenu.svelte';
	import Paginator from '$lib/components/Paginator.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import RenderTimeDuration from '$lib/components/RenderTimeDuration.svelte';
	import TaskbarName from '$lib/taskbar/TaskbarName.svelte';
	import TaskbarStatus from '$lib/taskbar/TaskbarStatus.svelte';
	import { taskStatus, type TaskShort, cancelTask, retryTask } from '$lib/taskstatus';
	import Eye from 'lucide-svelte/icons/eye';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import Ban from 'lucide-svelte/icons/ban';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Prefer the live store entry for a task when present, so running tasks on the
	// current page keep updating (state/progress) without a reload.
	let rows = $derived.by(() => {
		const overlaid = data.tasks.map((task): TaskShort => $taskStatus[task.id] ?? task);
		// Only the first page is the live "newest" view; deeper pages stay as loaded.
		if (data.page !== 1) return overlaid;
		// Surface brand-new tasks that arrived (via websocket) after the page loaded.
		const knownIds = new Set(data.tasks.map((task) => task.id));
		const newestLoaded = data.tasks[0]?.start_time ?? '';
		const fresh = Object.values($taskStatus).filter(
			(task) => !knownIds.has(task.id) && task.start_time > newestLoaded
		);
		return [...fresh, ...overlaid].sort((a, b) => (a.start_time < b.start_time ? 1 : -1));
	});

	// Page-local quick filter by task state (operates on the currently loaded page).
	let stateFilter = $state<'all' | 'running' | 'completed' | 'failed'>('all');
	let visibleRows = $derived(
		stateFilter === 'all' ? rows : rows.filter((task) => task.state === stateFilter)
	);
	const countByState = (state: TaskShort['state']) =>
		rows.filter((task) => task.state === state).length;

	// Row actions, consolidated into the kebab menu (mirrors TaskbarActions).
	const taskActions = (task: TaskShort): RowMenuItem[] => {
		const items: RowMenuItem[] = [
			{
				label: $t('taskbar.details'),
				icon: Eye,
				href: `/tasks/${task.id}${$pageStore.url.search}`
			}
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

	const goToPage = (newPage: number) => {
		const params = new URLSearchParams($pageStore.url.searchParams);
		params.set('page', newPage.toString());
		goto(`?${params.toString()}`, { noScroll: true, keepFocus: true });
	};

	// Make the task name navigate to its details page. The name can contain its
	// own device/config links, so ignore clicks that land on an inner anchor.
	const openTask = (event: MouseEvent, id: string) => {
		if ((event.target as HTMLElement).closest('a')) return;
		goto(`/tasks/${id}`);
	};
</script>

<Page title={$t('taskbar.page-title')} subtitle={$t('taskbar.page-subtitle')}>
	<FilterChips
		bind:selected={stateFilter}
		chips={[
			{ value: 'all', label: $t('taskbar.all'), count: rows.length },
			{
				value: 'running',
				label: $t('taskbar.running'),
				dot: 'info',
				count: countByState('running')
			},
			{
				value: 'completed',
				label: $t('taskbar.completed'),
				dot: 'online',
				count: countByState('completed')
			},
			{
				value: 'failed',
				label: $t('taskbar.failed'),
				dot: 'danger',
				count: countByState('failed')
			}
		]}
	/>

	<DataTable
		columns={[
			{ label: $t('taskbar.task-type') },
			{ label: $t('taskbar.status') },
			{ label: $t('taskbar.start-time') },
			{ label: $t('taskbar.duration') },
			{ label: $t('taskbar.actions'), align: 'right' }
		]}
		rows={visibleRows}
		empty={$t('taskbar.empty')}
	>
		{#snippet row(task)}
			<td>
				<div
					class="task-name w-fit"
					role="link"
					tabindex="0"
					onclick={(e) => openTask(e, task.id)}
					onkeydown={(e) => {
						if (e.key === 'Enter') goto(`/tasks/${task.id}`);
					}}
				>
					<TaskbarName
						globalState={data.globalState}
						deploymentInfos={data.deploymentInfos}
						{task}
					/>
				</div>
			</td>
			<td>
				<TaskbarStatus {task} showProgress={false} />
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
		{/snippet}
	</DataTable>

	{#if data.totalCount > data.perPage}
		<div class="mt-4 flex items-center justify-between gap-4">
			<span class="text-sm" style="color: var(--ds-text-mute)">
				{(data.page - 1) * data.perPage + 1}–{Math.min(data.page * data.perPage, data.totalCount)} / {data.totalCount}
			</span>
			<Paginator
				totalCount={data.totalCount}
				pageSize={data.perPage}
				page={data.page}
				onChange={goToPage}
			/>
		</div>
	{/if}
</Page>

<style lang="postcss">
	.task-name {
		cursor: pointer;
	}
	.task-name:hover {
		text-decoration: underline;
	}
</style>
