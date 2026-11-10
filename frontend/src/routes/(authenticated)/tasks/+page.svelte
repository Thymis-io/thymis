<script lang="ts">
	import { t } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { page as pageStore } from '$app/state';
	import type { PageData } from './$types';
	import Page from '#lib/components/layout/Page.svelte';
	import FilterChips from '#lib/components/layout/FilterChips.svelte';
	import Paginator from '#lib/components/Paginator.svelte';
	import TaskTable from '#lib/taskbar/TaskTable.svelte';
	import { taskStatus, type TaskShort } from '#lib/taskstatus.js';
	import { buildTaskTree, withLiveDescendants } from '#lib/taskTree.js';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	// Prefer the live store entry for a task when present, so running tasks on the
	// current page keep updating (state/progress) without a reload.
	let rows = $derived.by(() => {
		let loaded: TaskShort[] = data.tasks;
		// Only the first page is the live "newest" view; deeper pages stay as loaded.
		if (data.page === 1) {
			const knownIds = new Set(data.tasks.map((task) => task.id));
			const newestLoaded = data.tasks[0]?.submitted_time ?? '';
			const fresh = Object.values($taskStatus).filter(
				(task) =>
					!task.parent_task_id && !knownIds.has(task.id) && task.submitted_time > newestLoaded
			);
			loaded = [...fresh, ...data.tasks];
		}
		return withLiveDescendants(loaded, $taskStatus);
	});

	// Page-local quick filter by task state (operates on the currently loaded page).
	let stateFilter = $state<'all' | 'running' | 'completed' | 'failed'>('all');
	let roots = $derived(buildTaskTree(rows));
	const countByState = (state: TaskShort['state']) =>
		roots.filter((root) => root.task.state === state).length;

	const goToPage = (newPage: number) => {
		const params = new URLSearchParams(pageStore.url.search);
		params.set('page', newPage.toString());
		goto(`?${params.toString()}`, { reset: false });
	};
</script>

<Page title={$t('taskbar.page-title')} subtitle={$t('taskbar.page-subtitle')}>
	<FilterChips
		bind:selected={stateFilter}
		chips={[
			{ value: 'all', label: $t('taskbar.all'), count: roots.length },
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

	<TaskTable
		tasks={rows}
		globalState={data.globalState}
		filter={stateFilter === 'all' ? undefined : (root) => root.task.state === stateFilter}
	/>

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
