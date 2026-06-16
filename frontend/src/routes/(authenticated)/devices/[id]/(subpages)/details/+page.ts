import type { PageLoad } from './$types';
import { getConnectionHistory, getDeviceMetrics, getErrorLogs } from '$lib/deploymentInfo';

export const load: PageLoad = async ({ params, fetch, url }) => {
	const hours = url.searchParams.get('hours');
	const granularity = url.searchParams.get('granularity') as '1min' | '15min' | '1h' | null;
	const [connectionHistory, metrics, errorLogs] = await Promise.all([
		getConnectionHistory(fetch, params.id),
		getDeviceMetrics(fetch, params.id, hours ? parseInt(hours) : 24, granularity || '15min'),
		getErrorLogs(fetch, params.id)
	]);
	return { connectionHistory, metrics, errorLogs };
};
