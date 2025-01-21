import { getAllDeploymentInfosAsMapFromConfigId } from '$lib/deploymentInfo';
import type { PageLoad } from '../../$types';

export const load = (async ({ fetch }) => {
	const allDeploymentInfos = await getAllDeploymentInfosAsMapFromConfigId(fetch);
	return { allDeploymentInfos };
}) satisfies PageLoad;
