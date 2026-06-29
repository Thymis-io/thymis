import { getAllHardwareDevices } from '$lib/hardwareDevices';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch }) => {
	const hardwareDevices = await getAllHardwareDevices(fetch);
	return { hardwareDevices };
};
