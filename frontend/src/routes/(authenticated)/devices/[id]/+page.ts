import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import {
	getConnectionHistory,
	getDeploymentInfo,
	getDeviceMetrics,
	getErrorLogs
} from '$lib/deploymentInfo';

export const load: PageLoad = async ({ params, fetch, url }) => {
	const hours = url.searchParams.get('hours');
	const granularity = url.searchParams.get('granularity') as '1min' | '15min' | '1h' | null;
	const [deploymentInfo, connectionHistory, metrics, errorLogs] = await Promise.all([
		getDeploymentInfo(fetch, params.id),
		getConnectionHistory(fetch, params.id),
		getDeviceMetrics(fetch, params.id, hours ? parseInt(hours) : 24, granularity || '15min'),
		getErrorLogs(fetch, params.id)
	]);
	if (!deploymentInfo) {
		throw error(404, 'Device not found');
	}
	return { deploymentInfo, connectionHistory, metrics, errorLogs };
};
