import type { GitInfo } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const git_info_response = await fetch(`/api/git/info`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	return {
		gitInfo: (await git_info_response.json()) as GitInfo
	};
}) satisfies PageLoad;
