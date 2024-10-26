import type { Commit, GitInfo } from '$lib/history';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const history_response_p = fetch(`/api/history`, {
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

	const git_info_response_p = fetch(`/api/git/info`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	}).then((res) => {
		if (!res.ok) {
			throw new Error(`Failed to fetch git info: ${res.status} ${res.statusText}`);
		}
		return res.json() as Promise<GitInfo>;
	});
	const history_and_git_info = Promise.all([history_response_p, git_info_response_p]);
	return {
		history_and_git_info
	};
}) satisfies PageLoad;
