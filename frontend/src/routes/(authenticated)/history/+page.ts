import { handleFetch } from '$lib/fetchHandler';
import type { Commit } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const history_response = handleFetch(
		`/api/history`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		},
		{},
		fetch
	).then((res) => {
		if (res.ok) {
			return res.json() as Promise<Commit[]>;
		} else {
			return [];
		}
	});
	return {
		history: history_response
	};
}) satisfies PageLoad;
