import { getAllDeploymentInfos, getAllConnectedDeploymentInfos } from '$lib/deploymentInfo';
import { getFleetMetrics, getFleetConnectivity, getFleetDeviceMetricsLatest } from '$lib/fleet';
import type { Commit } from '$lib/history';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import type { PageLoad } from './$types';

type TimeWindow = '1h' | '24h' | '7d';
const hoursMap: Record<TimeWindow, number> = { '1h': 1, '24h': 24, '7d': 7 * 24 };
const granularityMap: Record<TimeWindow, '1min' | '15min' | '1h'> = {
	'1h': '1min',
	'24h': '15min',
	'7d': '1h'
};

export const load = (async ({ fetch, url }) => {
	const twParam = url.searchParams.get('timewindow');
	const timewindow: TimeWindow =
		twParam === '1h' || twParam === '24h' || twParam === '7d' ? twParam : '24h';
	const hours = hoursMap[timewindow];
	const granularity = granularityMap[timewindow];

	const [
		deploymentInfos,
		connectedDeploymentInfos,
		historyResponse,
		fleetMetrics,
		connectivity,
		topDevices
	] = await Promise.all([
		getAllDeploymentInfos(fetch),
		getAllConnectedDeploymentInfos(fetch),
		fetchWithNotify('/api/history', undefined, {}, fetch),
		getFleetMetrics(fetch, hours, granularity),
		getFleetConnectivity(fetch, hours, 48),
		getFleetDeviceMetricsLatest(fetch)
	]);

	const history = (await historyResponse.json()) as Commit[];
	const headCommit = history[0]?.SHA1 ?? null;

	return {
		deploymentInfos,
		connectedDeploymentInfos,
		headCommit,
		fleetMetrics,
		connectivity,
		topDevices,
		timewindow
	};
}) satisfies PageLoad;
