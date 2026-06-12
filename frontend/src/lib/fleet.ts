import { fetchWithNotify } from './fetchWithNotify';

export type FleetMetricPoint = {
	timestamp: string;
	cpu_avg: number;
	cpu_max: number;
	ram_avg: number;
	ram_max: number;
	disk_avg: number;
	disk_max: number;
	device_count: number;
};

export type ConnectivityPoint = {
	timestamp: string;
	connected_count: number;
};

export type FleetDeviceMetric = {
	deployment_info_id: string;
	name: string | null;
	cpu_percent: number;
	ram_percent: number;
	disk_percent: number;
	timestamp: string;
};

export const getFleetMetrics = async (
	fetch: typeof window.fetch,
	hours = 24,
	granularity: '1min' | '15min' | '1h' = '1h'
) => {
	const response = await fetchWithNotify(
		`/api/fleet/metrics?hours=${hours}&granularity=${granularity}`,
		undefined,
		{},
		fetch
	);
	if (response.ok) return (await response.json()) as FleetMetricPoint[];
	return [];
};

export const getFleetConnectivity = async (
	fetch: typeof window.fetch,
	hours = 24,
	buckets = 48
) => {
	const response = await fetchWithNotify(
		`/api/fleet/connectivity?hours=${hours}&buckets=${buckets}`,
		undefined,
		{},
		fetch
	);
	if (response.ok) return (await response.json()) as ConnectivityPoint[];
	return [];
};

export const getFleetDeviceMetricsLatest = async (fetch: typeof window.fetch) => {
	const response = await fetchWithNotify('/api/fleet/device_metrics_latest', undefined, {}, fetch);
	if (response.ok) return (await response.json()) as FleetDeviceMetric[];
	return [];
};
