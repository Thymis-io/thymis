import { getAllConnectedDeploymentInfos } from '$lib/deploymentInfo';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const allDeploymentInfos = await getAllConnectedDeploymentInfos(fetch);
	return { allDeploymentInfos };
}) satisfies PageLoad;
