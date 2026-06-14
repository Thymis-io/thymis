<script lang="ts">
	import { t } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { page as pageStore } from '$app/stores';
	import type { PageData } from './$types';
	import Page from '$lib/components/layout/Page.svelte';
	import DataTable from '$lib/components/layout/DataTable.svelte';
	import Paginator from '$lib/components/Paginator.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import RenderTimeDuration from '$lib/components/RenderTimeDuration.svelte';
	import TaskbarName from '$lib/taskbar/TaskbarName.svelte';
	import TaskbarStatus from '$lib/taskbar/TaskbarStatus.svelte';
	import TaskbarActions from '$lib/taskbar/TaskbarActions.svelte';
	import { taskStatus, type TaskShort } from '$lib/taskstatus';

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

	const goToPage = (newPage: number) => {
		const params = new URLSearchParams($pageStore.url.searchParams);
		params.set('page', newPage.toString());
		goto(`?${params.toString()}`, { noScroll: true, keepFocus: true });
	};
</script>

<Page title={$t('taskbar.page-title')} subtitle={$t('taskbar.page-subtitle')}>
	<DataTable
		columns={[
			{ label: $t('taskbar.task-type') },
			{ label: $t('taskbar.status') },
			{ label: $t('taskbar.start-time') },
			{ label: $t('taskbar.duration') },
			{ label: $t('taskbar.actions'), align: 'right' }
		]}
		{rows}
		empty={$t('taskbar.empty')}
	>
		{#snippet row(task)}
			<td>
				<TaskbarName globalState={data.globalState} deploymentInfos={data.deploymentInfos} {task} />
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
				<TaskbarActions {task} />
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
