import type { DefaultLogFields } from 'simple-git';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const response = await fetch('/api/history', {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	return {
		history: response.json() as Promise<DefaultLogFields[]>
	};
}) satisfies PageLoad;
