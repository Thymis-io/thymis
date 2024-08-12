import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const response = await fetch(`/api/history`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	return {
		history: response.json() as Promise<
			{ message: string; author: string; date: string; SHA: string; SHA1: string, state_diff: string[] }[]
		>
	};
}) satisfies PageLoad;
