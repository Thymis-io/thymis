import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { getDeploymentInfo } from '$lib/deploymentInfo';

export const load: PageLoad = async ({ params, fetch }) => {
	const deploymentInfo = await getDeploymentInfo(fetch, params.id);
	if (!deploymentInfo) {
		throw error(404, 'Device not found');
	}
	return { deploymentInfo };
};
