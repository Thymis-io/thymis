import { getAllDeploymentInfos } from '$lib/deploymentInfo';
import { getAllHardwareDevices } from '$lib/hardwareDevices';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const hardwareDevices = await getAllHardwareDevices(fetch);
	const deploymentInfos = await getAllDeploymentInfos(fetch);
	const loadTime = new Date().getTime();
	return {
		hardwareDevices,
		deploymentInfos,
		loadTime
	};
}) satisfies PageLoad;
