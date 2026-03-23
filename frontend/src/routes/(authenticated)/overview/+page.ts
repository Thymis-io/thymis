import { getAllDeploymentInfos, getAllConnectedDeploymentInfos } from '$lib/deploymentInfo';
import type { Commit } from '$lib/history';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const [deploymentInfos, connectedDeploymentInfos, historyResponse] = await Promise.all([
		getAllDeploymentInfos(fetch),
		getAllConnectedDeploymentInfos(fetch),
		fetchWithNotify('/api/history', undefined, {}, fetch)
	]);

	const history = (await historyResponse.json()) as Commit[];
	const headCommit = history[0]?.SHA1 ?? null;

	return {
		deploymentInfos,
		connectedDeploymentInfos,
		headCommit
	};
}) satisfies PageLoad;
