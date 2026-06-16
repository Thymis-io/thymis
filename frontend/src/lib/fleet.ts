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

export type Granularity = '1min' | '15min' | '1h' | '6h' | '1d';
export type TimeRange = '24h' | '7d' | '30d' | '90d';

export const RANGE_OPTIONS: TimeRange[] = ['24h', '7d', '30d', '90d'];

export const rangeToParams = (
	range: TimeRange
): { hours: number; granularity: Granularity; buckets: number } => {
	switch (range) {
		case '24h':
			return { hours: 24, granularity: '15min', buckets: 48 };
		case '7d':
			return { hours: 168, granularity: '1h', buckets: 48 };
		case '30d':
			return { hours: 720, granularity: '6h', buckets: 60 };
		case '90d':
			return { hours: 2160, granularity: '1d', buckets: 90 };
	}
};

// Custom range: clamp an arbitrary hour span to a sane granularity/buckets.
export const hoursToParams = (
	hours: number
): { hours: number; granularity: Granularity; buckets: number } => {
	const h = Math.max(1, Math.min(2160, Math.round(hours)));
	if (h <= 24) return { hours: h, granularity: '15min', buckets: 48 };
	if (h <= 168) return { hours: h, granularity: '1h', buckets: 48 };
	if (h <= 720) return { hours: h, granularity: '6h', buckets: 60 };
	return { hours: h, granularity: '1d', buckets: 90 };
};

export type DeviceAvailabilityRow = {
	deployment_info_id: string;
	name: string | null;
	states: boolean[];
};

export type FleetAvailability = {
	timestamps: string[];
	devices: DeviceAvailabilityRow[];
};

export type FleetAlert = {
	deployment_info_id: string;
	name: string | null;
	kind: 'offline' | 'flapping' | 'cpu' | 'ram' | 'disk';
	severity: 'warning' | 'critical';
	detail: string;
	value: number | null;
};

export const getFleetAvailability = async (
	fetch: typeof window.fetch,
	hours = 24,
	buckets = 48
) => {
	const response = await fetchWithNotify(
		`/api/fleet/availability?hours=${hours}&buckets=${buckets}`,
		undefined,
		{},
		fetch
	);
	if (response.ok) return (await response.json()) as FleetAvailability;
	return { timestamps: [], devices: [] } as FleetAvailability;
};

export const getFleetAlerts = async (fetch: typeof window.fetch) => {
	const response = await fetchWithNotify('/api/fleet/alerts', undefined, {}, fetch);
	if (response.ok) return (await response.json()) as FleetAlert[];
	return [] as FleetAlert[];
};
