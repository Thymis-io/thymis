import { fetchWithNotify } from './fetchWithNotify';
import type { HardwareDevice } from './hardwareDevices';

export const ONLINE_THRESHOLD_MS = 30 * 1000;
export const STALE_THRESHOLD_MS = 7 * 24 * 60 * 60 * 1000;

export const isOnline = (lastSeen: string | null): boolean =>
	!!lastSeen && Date.now() - new Date(lastSeen).getTime() < ONLINE_THRESHOLD_MS;

export const isActive = (lastSeen: string | null): boolean =>
	!!lastSeen && Date.now() - new Date(lastSeen).getTime() < STALE_THRESHOLD_MS;

export type NetworkInterface = {
	interface: string;
	ipv4_addresses: string[];
	ipv6_addresses: string[];
	mac_address: string | null;
};

export type DeploymentInfo = {
	id: string;
	ssh_public_key: string;
	deployed_config_commit: string | null;
	deployed_config_id: string | null;
	reachable_deployed_host: string | null;
	last_seen: string | null;
	first_seen: string | null;
	hardware_devices: HardwareDevice[];
	network_interfaces?: NetworkInterface[] | null;
	location?: string | null;
	name?: string | null;
};

export type ConnectionHistoryEntry = {
	id: string;
	connected_at: string;
	disconnected_at?: string;
};

export type DeviceMetricsEntry = {
	timestamp: string;
	cpu_percent: number;
	ram_percent: number;
	disk_percent: number;
};

export type ErrorLogEntry = {
	timestamp: string;
	message: string;
	severity: number;
	syslogtag: string;
};

export const getDeploymentInfoByConfigId = async (
	fetch: typeof window.fetch,
	deployedConfigId: string
) => {
	const response = await fetchWithNotify(
		`/api/deployment_infos_by_config_id/${deployedConfigId}`,
		undefined,
		{ 404: `Deployment info not found for config id ${deployedConfigId}` },
		fetch
	);
	if (response.ok) {
		const deploymentInfos = await response.json();
		if (deploymentInfos.length == 1) {
			return deploymentInfos[0] as DeploymentInfo;
		} else if (deploymentInfos.length > 1) {
			console.error(
				`Multiple deployment infos found for config id ${deployedConfigId}, using the first one`
			);
			return deploymentInfos[0] as DeploymentInfo;
		}
	}
};

export const getDeploymentInfosByConfigId = async (
	fetch: typeof window.fetch,
	deployedConfigId: string
) => {
	const response = await fetchWithNotify(
		`/api/deployment_infos_by_config_id/${deployedConfigId}`,
		undefined,
		{ 404: `Deployment info not found for config id ${deployedConfigId}` },
		fetch
	);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getConnectedDeploymentInfosByConfigId = async (
	fetch: typeof window.fetch,
	deployedConfigId: string
) => {
	const response = await fetchWithNotify(
		`/api/connected_deployment_infos_by_config_id/${deployedConfigId}`,
		undefined,
		{ 404: `Deployment info not found for config id ${deployedConfigId}` },
		fetch
	);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getAllDeploymentInfos = async (fetch: typeof window.fetch) => {
	const response = await fetchWithNotify('/api/all_deployment_infos', undefined, {}, fetch);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getAllConnectedDeploymentInfos = async (fetch: typeof window.fetch) => {
	const response = await fetchWithNotify(
		'/api/all_connected_deployment_info',
		undefined,
		{},
		fetch
	);
	if (response.ok) {
		return (await response.json()) as DeploymentInfo[];
	}
	return [];
};

export const getAllDeploymentInfosAsMapFromConfigId = async (fetch: typeof window.fetch) => {
	const deploymentInfos = await getAllDeploymentInfos(fetch);
	const deploymentInfosMap = new Map<string, DeploymentInfo[]>();
	for (const deploymentInfo of deploymentInfos) {
		const configId = deploymentInfo.deployed_config_id;
		if (!configId) {
			continue;
		}
		if (deploymentInfosMap.has(configId)) {
			deploymentInfosMap.get(configId)?.push(deploymentInfo);
		} else {
			deploymentInfosMap.set(configId, [deploymentInfo]);
		}
	}
	return deploymentInfosMap;
};

export const getDeploymentInfo = async (fetch: typeof window.fetch, id: string) => {
	const response = await fetchWithNotify(
		`/api/deployment_info/${id}`,
		undefined,
		{ 404: 'Device not found' },
		fetch
	);
	if (response.ok) return (await response.json()) as DeploymentInfo;
	return null;
};

export const getConnectionHistory = async (fetch: typeof window.fetch, id: string) => {
	const response = await fetchWithNotify(
		`/api/deployment_info/${id}/connection_history`,
		undefined,
		{},
		fetch
	);
	if (response.ok) return (await response.json()) as ConnectionHistoryEntry[];
	return [];
};

export const getDeviceMetrics = async (
	fetch: typeof window.fetch,
	id: string,
	hours: number = 168,
	granularity: '1min' | '15min' | '1h' = '1h'
) => {
	const response = await fetchWithNotify(
		`/api/deployment_info/${id}/metrics?hours=${hours}&granularity=${granularity}`,
		undefined,
		{},
		fetch
	);
	if (response.ok) return (await response.json()) as DeviceMetricsEntry[];
	return [];
};

export const getErrorLogs = async (fetch: typeof window.fetch, id: string) => {
	const response = await fetchWithNotify(
		`/api/deployment_info/${id}/error_logs`,
		undefined,
		{},
		fetch
	);
	if (response.ok) return (await response.json()) as ErrorLogEntry[];
	return [];
};

export type DeploymentInfoUpdate = {
	ssh_public_key?: string | null;
	deployed_config_id?: string | null;
	reachable_deployed_host?: string | null;
	name?: string | null;
	location?: string | null;
};

export const updateDeploymentInfo = async (
	fetch: typeof window.fetch,
	id: string,
	update: DeploymentInfoUpdate
) => {
	return fetchWithNotify(
		`/api/deployment_info/${id}`,
		{
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(update)
		},
		{},
		fetch
	);
};
