import type { PageLoad, PageParentData } from './$types';
import type { Commit } from '$lib/history';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch, url, parent }) => {
	const identifier = url.searchParams.get('global-nav-target');
	if (identifier) {
		const [parentData, historyResponse] = await Promise.all([
			parent() as Promise<PageParentData>,
			fetchWithNotify('/api/history', undefined, {}, fetch)
		]);
		// if config is not in parentData state, redirect to '/configuration/list'
		if (!parentData.globalState.configs.find((config) => config.identifier === identifier)) {
			redirect(303, '/configuration/list');
		}
		const history = (await historyResponse.json()) as Commit[];
		const headCommit = history[0]?.SHA1 ?? null;
		return { headCommit };
	} else {
		throw new Error('No identifier provided');
	}
};
