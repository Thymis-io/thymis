import type { PageLoad } from './$types';
import { getLogs } from '$lib/logs';
import { error } from '@sveltejs/kit';

export const load = (async ({ params, fetch, url }) => {
	try {
		const fromDateTime = url.searchParams.get('fromDateTime');
		const toDateTime = url.searchParams.get('toDateTime');
		// default to is now
		// default from is to-1h
		const to = toDateTime ? new Date(toDateTime) : new Date();
		const from = fromDateTime ? new Date(fromDateTime) : new Date(to.getTime() - 60 * 60 * 1000);
		// default to 1000
		const limit = url.searchParams.get('limit')
			? parseInt(url.searchParams.get('limit') ?? '1000')
			: 1000;
		// default to 0
		const offset = url.searchParams.get('offset')
			? parseInt(url.searchParams.get('offset') ?? '0')
			: 0;
		const logs = await getLogs(fetch, params.id, to, from, limit, offset);
		return {
			logs
		};
	} catch (e) {
		error(404, 'Task not found');
	}
}) satisfies PageLoad;
