import type { PageLoad } from './$types';
import type { RegisteredDevice } from '$lib/hostkey';

export const load: PageLoad = async ({ fetch }) => {
	const res = await fetch(`/api/devices`);
	const registeredDevices: RegisteredDevice[] = await res.json();

	return {
		registeredDevices
	};
};
