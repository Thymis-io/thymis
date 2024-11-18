import type { GitInfo } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const git_info_response = fetch(`/api/git/info`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	return {
		gitInfo: (await new Promise((resolve, reject) => {
			git_info_response
				.then((res) => res.json())
				.then((json) => resolve(json as GitInfo))
				.catch(reject);
		})) as GitInfo
	};
}) satisfies PageLoad;
