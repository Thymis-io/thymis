import type { Commit } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const history_response = fetch(`/api/history`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	}).then((res) => {
		if (!res.ok) {
			throw new Error(`Failed to fetch history: ${res.status} ${res.statusText}`);
		}
		return res.json() as Promise<Commit[]>;
	});
	return {
		history: history_response
	};
}) satisfies PageLoad;
