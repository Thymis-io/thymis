import { getAllHardwareDevices } from '$lib/hardwareDevices';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const hardwareDevices = await getAllHardwareDevices(fetch);
	return {
		hardwareDevices
	};
}) satisfies PageLoad;
