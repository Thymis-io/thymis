import { getAllDeploymentInfos } from '$lib/deploymentInfo';
import { getAllHardwareDevices } from '$lib/hardwareDevices';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const hardwareDevices = await getAllHardwareDevices(fetch);
	const deploymentInfos = await getAllDeploymentInfos(fetch);
	return {
		hardwareDevices,
		deploymentInfos
	};
}) satisfies PageLoad;
