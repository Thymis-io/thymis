import type { PageLoad, PageParentData } from './$types';
import { getConnectedDeploymentInfosByConfigId, type DeploymentInfo } from '$lib/deploymentInfo';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch, url, parent }) => {
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	if (identifier) {
		deploymentInfos = await getConnectedDeploymentInfosByConfigId(fetch, identifier);
		const parentData: PageParentData = await parent();
		// if config is not in parentData state, redirect to '/configuration/list'
		if (!parentData.globalState.configs.find((config) => config.identifier === identifier)) {
			redirect(303, '/configuration/list');
		}
		return { deploymentInfos: deploymentInfos };
	} else {
		throw new Error('No identifier provided');
	}
};
