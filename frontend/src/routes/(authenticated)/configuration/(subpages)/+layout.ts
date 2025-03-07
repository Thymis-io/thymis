import type { LayoutLoad } from './$types';
import {
	getAllConnectedDeploymentInfos,
	getConnectedDeploymentInfosByConfigId,
	type DeploymentInfo
} from '$lib/deploymentInfo';
import { redirect } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ fetch, url, parent }) => {
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	const identifierType = url.searchParams.get('global-nav-target-type');
	if (identifier && identifierType && identifierType === 'config') {
		deploymentInfos = await getConnectedDeploymentInfosByConfigId(fetch, identifier);
		return { deploymentInfos: deploymentInfos };
	} else if (identifier && identifierType && identifierType === 'tag') {
		const { globalState } = await parent();
		const configIds = globalState.configs
			.filter((config) => config.tags.includes(identifier))
			.map((config) => config.identifier);
		const allConnectedDeploymentInfos = await getAllConnectedDeploymentInfos(fetch);
		deploymentInfos = allConnectedDeploymentInfos.filter(
			(deploymentInfo) =>
				deploymentInfo.deployed_config_id && configIds.includes(deploymentInfo.deployed_config_id)
		);
		return { deploymentInfos: deploymentInfos };
	} else {
		redirect(303, '/overview?error-message=No%20config%20id%20provided');
	}
};
