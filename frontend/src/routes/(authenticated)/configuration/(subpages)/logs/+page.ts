import { getLogs, getProgramNames } from '$lib/logs';
import type { PageLoad } from './$types';

export const load = (async ({ fetch, url, parent }) => {
	const { deploymentInfos } = await parent();

	let deploymentInfoId = url.searchParams.get('deployment-info-id');
	const programName = url.searchParams.get('program-name');
	const exactProgramName = url.searchParams.get('exact-program-name') === 'true';

	if (!deploymentInfos.find((info) => info.id === deploymentInfoId)) {
		deploymentInfoId = deploymentInfos.length > 0 ? deploymentInfos[0].id : null;
	}

	let logs;
	let programNames;

	if (deploymentInfoId) {
		logs = await getLogs(fetch, deploymentInfoId, null, null, programName, exactProgramName, 40, 0);
		programNames = await getProgramNames(fetch, deploymentInfoId);
	}

	return {
		logs: logs?.logs ?? [],
		totalLogCount: logs?.total_count ?? 0,
		programNames: programNames
	};
}) satisfies PageLoad;
