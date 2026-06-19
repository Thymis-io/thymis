import { getAllDeploymentInfos } from '$lib/deploymentInfo';
import { getAllHardwareDevices } from '$lib/hardwareDevices';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch }) => {
	const [deploymentInfos, hardwareDevices] = await Promise.all([
		getAllDeploymentInfos(fetch),
		getAllHardwareDevices(fetch)
	]);
	return { deploymentInfos, hardwareDevices };
};
