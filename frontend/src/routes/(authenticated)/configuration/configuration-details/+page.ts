import type { PageLoad } from './$types';
import { getDeploymentInfosByConfigId, type DeploymentInfo } from '$lib/deploymentInfo';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch, url }) => {
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	if (identifier) {
		deploymentInfos = await getDeploymentInfosByConfigId(fetch, identifier);
		if (deploymentInfos.length === 0) {
			redirect(302, '/devices');
		}
		return { deploymentInfos: deploymentInfos };
	} else {
		throw new Error('No identifier provided');
	}
};
