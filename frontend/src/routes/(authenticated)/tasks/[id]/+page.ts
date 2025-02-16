import type { PageLoad } from './$types';
import { getTask } from '$lib/taskstatus';
import { error } from '@sveltejs/kit';

export const load = (async ({ params, fetch }) => {
	try {
		const task = await getTask(params.id, fetch);
		return {
			task,
			task_id: params.id
		};
	} catch (e) {
		error(404, 'Task not found');
	}
}) satisfies PageLoad;
