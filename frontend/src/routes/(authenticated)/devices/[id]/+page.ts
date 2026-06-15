import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import {
	getAllConnectedDeploymentInfos,
	getConnectionHistory,
	getDeploymentInfo,
	getDeviceMetrics,
	getErrorLogs
} from '$lib/deploymentInfo';
import { getLogs, getProgramNames } from '$lib/logs';

export const load: PageLoad = async ({ params, fetch, url }) => {
	const hours = url.searchParams.get('hours');
	const granularity = url.searchParams.get('granularity') as '1min' | '15min' | '1h' | null;
	const programName = url.searchParams.get('program-name');
	const exactProgramName = url.searchParams.get('exact-program-name') === 'true';
	const [
		deploymentInfo,
		connectionHistory,
		metrics,
		errorLogs,
		connectedDeploymentInfos,
		logs,
		programNames
	] = await Promise.all([
		getDeploymentInfo(fetch, params.id),
		getConnectionHistory(fetch, params.id),
		getDeviceMetrics(fetch, params.id, hours ? parseInt(hours) : 24, granularity || '15min'),
		getErrorLogs(fetch, params.id),
		getAllConnectedDeploymentInfos(fetch),
		getLogs(fetch, params.id, null, null, programName, exactProgramName, 40, 0),
		getProgramNames(fetch, params.id)
	]);
	if (!deploymentInfo) {
		throw error(404, 'Device not found');
	}
	// whether the agent currently has a live relay connection (needed for VNC/terminal)
	const connected = connectedDeploymentInfos.some((info) => info.id === params.id);
	return {
		deploymentInfo,
		connectionHistory,
		metrics,
		errorLogs,
		connected,
		logs: logs?.logs ?? [],
		programNames
	};
};
