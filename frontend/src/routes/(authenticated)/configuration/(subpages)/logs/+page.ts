import { getLogs } from '$lib/logs';
import type { PageLoad } from './$types';

export const load = (async ({ fetch, url, parent }) => {
	const { deploymentInfos } = await parent();

	let deploymentInfoId = url.searchParams.get('deployment-info-id');

	if (!deploymentInfos.find((info) => info.id === deploymentInfoId)) {
		deploymentInfoId = deploymentInfos.length > 0 ? deploymentInfos[0].id : null;
	}

	const logs = deploymentInfoId
		? await getLogs(fetch, deploymentInfoId, null, null, 40, 0)
		: { total_count: 0, logs: [] };

	return {
		logs: logs.logs,
		total_count: logs.total_count
	};
}) satisfies PageLoad;
