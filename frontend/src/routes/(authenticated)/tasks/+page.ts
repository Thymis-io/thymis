import type { PageLoad } from './$types';
import { getAllTasks } from '$lib/taskstatus';

export const load = (async ({ url, fetch }) => {
	const perPage = 50;
	const page = Math.max(parseInt(url.searchParams.get('page') || '1'), 1);
	const { tasks, totalCount } = await getAllTasks(perPage, (page - 1) * perPage, fetch);
	return {
		tasks,
		totalCount: parseInt(totalCount || '0'),
		page,
		perPage
	};
}) satisfies PageLoad;
