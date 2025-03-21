import { error } from '@sveltejs/kit';
import { getHardwareDeviceById } from '$lib/hardwareDevices';
import { getAllDeploymentInfos } from '$lib/deploymentInfo';
import type { PageLoad } from './$types';

export const load = (async ({ params, fetch, parent }) => {
	const id = params.id;

	try {
		const device = await getHardwareDeviceById(id, fetch);
		if (!device) {
			throw error(404, 'Device not found');
		}

		const deploymentInfos = await getAllDeploymentInfos(fetch);
		const deviceDeploymentInfo = device.deployment_info_id
			? deploymentInfos.find((d) => d.id === device.deployment_info_id)
			: undefined;

		// Get parent data (layout data with navigation and global state)
		const data = await parent();

		return {
			device,
			deploymentInfos,
			deviceDeploymentInfo,
			data,
			loadTime: new Date().getTime()
		};
	} catch (e) {
		console.error(e);
		throw error(404, 'Device not found');
	}
}) satisfies PageLoad;
