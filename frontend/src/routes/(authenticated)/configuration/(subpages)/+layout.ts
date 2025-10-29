import type { LayoutLoad } from './$types';
import {
	getAllConnectedDeploymentInfos,
	getAllDeploymentInfos,
	getConnectedDeploymentInfosByConfigId,
	getDeploymentInfosByConfigId,
	type DeploymentInfo
} from '$lib/deploymentInfo';
import { redirect } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ fetch, url, parent }) => {
	let connectedDeploymentInfos: DeploymentInfo[];
	let deploymentInfos: DeploymentInfo[];
	const identifier = url.searchParams.get('global-nav-target');
	const identifierType = url.searchParams.get('global-nav-target-type');

	if (identifier && identifierType && identifierType === 'config') {
		connectedDeploymentInfos = await getConnectedDeploymentInfosByConfigId(fetch, identifier);
		deploymentInfos = await getDeploymentInfosByConfigId(fetch, identifier);
	} else if (identifier && identifierType && identifierType === 'tag') {
		const { globalState } = await parent();
		const configIds = globalState.configs
			.filter((config) => config.tags.includes(identifier))
			.map((config) => config.identifier);
		const allConnectedDeploymentInfos = await getAllConnectedDeploymentInfos(fetch);
		const allDeploymentInfos = await getAllDeploymentInfos(fetch);
		connectedDeploymentInfos = allConnectedDeploymentInfos.filter(
			(deploymentInfo) =>
				deploymentInfo.deployed_config_id && configIds.includes(deploymentInfo.deployed_config_id)
		);
		deploymentInfos = allDeploymentInfos.filter(
			(deploymentInfo) =>
				deploymentInfo.deployed_config_id && configIds.includes(deploymentInfo.deployed_config_id)
		);
	} else {
		redirect(303, '/overview?error-message=No%20config%20id%20provided');
	}

	return { connectedDeploymentInfos: connectedDeploymentInfos, deploymentInfos: deploymentInfos };
};
