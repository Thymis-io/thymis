import { redirect } from '@sveltejs/kit';
import { getLogs, getProgramNames } from '$lib/logs';
import type { PageLoad } from './$types';

export const load = (async ({ fetch, url, parent }) => {
	const { deploymentInfos } = await parent();

	let deploymentInfoId = url.searchParams.get('deployment-info-id');
	const programName = url.searchParams.get('program-name');
	const exactProgramName = url.searchParams.get('exact-program-name') === 'true';

	if (!deploymentInfos.find((info) => info.id === deploymentInfoId) && deploymentInfos.length > 0) {
		const orderedInfos = deploymentInfos.toSorted(
			(a, b) =>
				(b.last_seen ? new Date(b.last_seen).getTime() : -1000) -
				(a.last_seen ? new Date(a.last_seen).getTime() : -1000)
		);
		deploymentInfoId = orderedInfos[0].id;
		const searchParams = new URLSearchParams(url.searchParams);
		searchParams.set('deployment-info-id', deploymentInfoId);
		redirect(307, `/configuration/logs?${searchParams.toString()}`);
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
