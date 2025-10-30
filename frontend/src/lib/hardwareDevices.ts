import { t } from 'svelte-i18n';
import { get } from 'svelte/store';
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

export const calcTimeSince = (date: Date, currentDate: Date, minSeconds = 0) => {
	const seconds = Math.max(minSeconds, Math.floor((currentDate.getTime() - date.getTime()) / 1000));
	let interval = seconds / (60 * 60 * 24 * 365);
	if (interval > 1) return get(t)('time.ago.year', { values: { count: Math.floor(interval) } });
	interval = seconds / (60 * 60 * 24 * 30);
	if (interval > 1) return get(t)('time.ago.month', { values: { count: Math.floor(interval) } });
	interval = seconds / (60 * 60 * 24 * 7);
	if (interval > 1) return get(t)('time.ago.week', { values: { count: Math.floor(interval) } });
	interval = seconds / (60 * 60 * 24);
	if (interval > 1) return get(t)('time.ago.day', { values: { count: Math.floor(interval) } });
	interval = seconds / (60 * 60);
	if (interval > 1) return get(t)('time.ago.hour', { values: { count: Math.floor(interval) } });
	interval = seconds / 60;
	if (interval > 1) return get(t)('time.ago.minute', { values: { count: Math.floor(interval) } });
	return get(t)('time.ago.second', { values: { count: Math.floor(seconds) } });
};
