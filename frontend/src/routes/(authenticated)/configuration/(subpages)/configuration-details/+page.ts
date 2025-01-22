import type { PageLoad, PageParentData } from './$types';
import { getDeploymentInfosByConfigId, type DeploymentInfo } from '$lib/deploymentInfo';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch, url, parent }) => {
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	if (identifier) {
		deploymentInfos = await getDeploymentInfosByConfigId(fetch, identifier);
		const parentData: PageParentData = await parent();
		// if config is not in parentData state, redirect to '/devices'
		if (!parentData.state.devices.find((device) => device.identifier === identifier)) {
			redirect(303, '/configuration/list');
		}
		return { deploymentInfos: deploymentInfos };
	} else {
		throw new Error('No identifier provided');
	}
};
