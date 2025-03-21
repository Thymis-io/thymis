import { fetchWithNotify } from './fetchWithNotify';

export type HardwareDevice = {
	id: string;
	hardware_ids: Record<string, string>;
	deployment_info_id: string | undefined;
	last_seen: string;
};

export const getAllHardwareDevices = async (fetch: typeof window.fetch = window.fetch) => {
	const response = await fetchWithNotify('/api/hardware_device', undefined, {}, fetch);
	return (await response.json()) as HardwareDevice[];
};

export const getHardwareDeviceById = async (
	id: string,
	fetch: typeof window.fetch = window.fetch
) => {
	const response = await fetchWithNotify(`/api/hardware_device/${id}`, undefined, {}, fetch);
	return (await response.json()) as HardwareDevice;
};
