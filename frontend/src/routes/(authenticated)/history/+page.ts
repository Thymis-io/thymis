import { fetchWithNotify } from '$lib/fetchWithNotify';
import type { Commit } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const history_response = await fetchWithNotify(
		`/api/history`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		},
		{},
		fetch
	);
	return {
		history: (await history_response.json()) as Commit[]
	};
}) satisfies PageLoad;
