import { fetchWithNotify } from '$lib/fetchWithNotify';
import type { PageLoad } from './$types';

type ExternalRepositoryStatus = {
	status: 'no-path' | 'no-readme' | 'no-magic-string' | 'loaded';
	modules: string[];
	details?: string;
};

const getExternalRepositoriesStatus = async (fetch: typeof window.fetch) => {
	const response = await fetchWithNotify('/api/external-repositories/status', undefined, {}, fetch);
	if (response.ok) {
		return (await response.json()) as Record<string, ExternalRepositoryStatus>;
	}
	return {};
};

export const load = (async ({ fetch }) => {
	const externalRepositoriesStatus = await getExternalRepositoriesStatus(fetch);
	return {
		externalRepositoriesStatus
	};
}) satisfies PageLoad;
