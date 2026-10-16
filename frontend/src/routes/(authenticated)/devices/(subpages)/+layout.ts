import { getAllHardwareDevices } from '$lib/hardwareDevices';
import { getPairingCodes } from '$lib/pairingCodes';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch }) => {
	const [hardwareDevices, pairingCodes] = await Promise.all([
		getAllHardwareDevices(fetch),
		getPairingCodes(fetch)
	]);
	return { hardwareDevices, pairingCodes };
};
