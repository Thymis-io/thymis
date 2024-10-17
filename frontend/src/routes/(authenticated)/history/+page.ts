import type { Commit, GitInfo } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const history_response = fetch(`/api/history`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	const git_info_response = fetch(`/api/git/info`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	return {
		history: new Promise((resolve, reject) => {
			history_response
				.then((res) => res.json())
				.then((json) => resolve(json as Commit[]))
				.catch(reject);
		}) as Promise<Commit[]>,
		gitInfo: new Promise((resolve, reject) => {
			git_info_response
				.then((res) => res.json())
				.then((json) => resolve(json as GitInfo))
				.catch(reject);
		}) as Promise<GitInfo>
	};
}) satisfies PageLoad;
