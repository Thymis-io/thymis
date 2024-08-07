import type { PageLoad } from './$types';
import { taskStatusValue } from '$lib/taskstatus';
import { error } from '@sveltejs/kit';

export const load = (async ({ params }) => {
	// if taskStatusValue[params.id] is not defined, 404
	if (!taskStatusValue[Number(params.id)]) {
		error(404, 'Not found');
	}
	return {};
}) satisfies PageLoad;
