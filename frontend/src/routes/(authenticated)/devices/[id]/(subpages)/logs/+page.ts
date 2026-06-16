import type { PageLoad } from './$types';
import { getLogs, getProgramNames } from '$lib/logs';

export const load: PageLoad = async ({ params, fetch, url }) => {
	const programName = url.searchParams.get('program-name');
	const exactProgramName = url.searchParams.get('exact-program-name') === 'true';
	const [logs, programNames] = await Promise.all([
		getLogs(fetch, params.id, null, null, programName, exactProgramName, 40, 0),
		getProgramNames(fetch, params.id)
	]);
	return { logs: logs?.logs ?? [], programNames };
};
