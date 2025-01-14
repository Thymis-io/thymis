import type { PageLoad } from './$types';
import { getDeploymentInfosByConfigId, type DeploymentInfo } from '$lib/deploymentInfo';

export const load: PageLoad = async ({ fetch, url }) => {
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	if (identifier) {
		deploymentInfos = await getDeploymentInfosByConfigId(fetch, identifier);
		return { deploymentInfos: deploymentInfos };
	} else {
		throw new Error('No identifier provided');
	}
};
