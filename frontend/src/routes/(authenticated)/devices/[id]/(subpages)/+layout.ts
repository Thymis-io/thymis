import type { LayoutLoad } from './$types';
import { getDeploymentInfo, getAllConnectedDeploymentInfos } from '$lib/deploymentInfo';
import { error } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ params, fetch }) => {
	const [deploymentInfo, connectedDeploymentInfos] = await Promise.all([
		getDeploymentInfo(fetch, params.id),
		getAllConnectedDeploymentInfos(fetch)
	]);
	if (!deploymentInfo) {
		error(404, 'Device not found');
	}
	const connected = connectedDeploymentInfos.some((info) => info.id === params.id);
	return { deploymentInfo, connected };
};
