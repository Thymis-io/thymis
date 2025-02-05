import type { LayoutLoad } from './$types';
import { getConnectedDeploymentInfosByConfigId, type DeploymentInfo } from '$lib/deploymentInfo';
import { redirect } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ fetch, url }) => {
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	const identifierType = url.searchParams.get('global-nav-target-type');
	if (identifier && identifierType && identifierType === 'config') {
		deploymentInfos = await getConnectedDeploymentInfosByConfigId(fetch, identifier);
		return { deploymentInfos: deploymentInfos };
	} else if (identifier && identifierType && identifierType === 'tag') {
		return;
	} else {
		redirect(303, '/overview?error-message=No%20config%20id%20provided');
	}
};
