import { getAllDeploymentInfos, getAllConnectedDeploymentInfos } from '$lib/deploymentInfo';
import {
	getFleetConnectivity,
	getFleetMetricsLatest,
	getFleetAvailability,
	getFleetAlerts,
	rangeToParams,
	hoursToParams,
	RANGE_OPTIONS,
	type TimeRange
} from '$lib/fleet';
import type { Commit } from '$lib/history';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import type { PageLoad } from './$types';

export const load = (async ({ fetch, url }) => {
	const rangeParam = url.searchParams.get('range');
	const customHoursParam = url.searchParams.get('hours');

	let range: TimeRange | 'custom';
	let params: { hours: number; granularity: string; buckets: number };

	if (customHoursParam && !RANGE_OPTIONS.includes(rangeParam as TimeRange)) {
		range = 'custom';
		params = hoursToParams(Number(customHoursParam));
	} else {
		range = RANGE_OPTIONS.includes(rangeParam as TimeRange) ? (rangeParam as TimeRange) : '24h';
		params = rangeToParams(range);
	}

	const [
		deploymentInfos,
		connectedDeploymentInfos,
		historyResponse,
		connectivity,
		topDevices,
		availability,
		alerts
	] = await Promise.all([
		getAllDeploymentInfos(fetch),
		getAllConnectedDeploymentInfos(fetch),
		fetchWithNotify('/api/history', undefined, {}, fetch),
		getFleetConnectivity(fetch, params.hours, params.buckets),
		getFleetMetricsLatest(fetch),
		getFleetAvailability(fetch, params.hours, params.buckets),
		getFleetAlerts(fetch)
	]);

	const history = (await historyResponse.json()) as Commit[];
	const headCommit = history[0]?.SHA1 ?? null;

	return {
		deploymentInfos,
		connectedDeploymentInfos,
		headCommit,
		connectivity,
		topDevices,
		availability,
		alerts,
		range,
		customHours: params.hours
	};
}) satisfies PageLoad;
