import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ url, parent }) => {
	const { globalState } = await parent();
	const identifier = url.searchParams.get('global-nav-target');
	const identifierType = url.searchParams.get('global-nav-target-type');

	let deploymentInfos;

	if (identifier && identifierType && identifierType === 'config') {
		deploymentInfos = globalState.deploymentInfos.filter(
			(d) => d.deployed_config_id === identifier
		);
	} else if (identifier && identifierType && identifierType === 'tag') {
		const configIds = globalState.configs
			.filter((config) => config.tags.includes(identifier))
			.map((config) => config.identifier);
		deploymentInfos = globalState.deploymentInfos.filter(
			(deploymentInfo) =>
				deploymentInfo.deployed_config_id && configIds.includes(deploymentInfo.deployed_config_id)
		);
	} else {
		redirect(303, '/overview?error-message=No%20config%20id%20provided');
	}

	return { deploymentInfos };
};
