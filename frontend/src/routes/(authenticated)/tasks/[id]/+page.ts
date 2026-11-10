import type { PageLoad } from './$types';
import { getSubtasks, getTask } from '#lib/taskstatus.js';
import { error } from '@sveltejs/kit';

export const load = (async ({ params, fetch }) => {
	try {
		const [task, subtasks] = await Promise.all([
			getTask(params.id, fetch),
			getSubtasks(params.id, fetch)
		]);
		return {
			task,
			subtasks,
			task_id: params.id
		};
	} catch (e) {
		error(404, 'Task not found');
	}
}) satisfies PageLoad;
