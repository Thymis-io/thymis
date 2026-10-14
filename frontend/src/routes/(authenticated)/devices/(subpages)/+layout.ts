import { getAllHardwareDevices } from '#lib/hardwareDevices.js';
import { getPairingCodes } from '#lib/pairingCodes.js';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch }) => {
	const [hardwareDevices, pairingCodes] = await Promise.all([
		getAllHardwareDevices(fetch),
		getPairingCodes(fetch)
	]);
	return { hardwareDevices, pairingCodes };
};
