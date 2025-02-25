import type { PageLoad } from './$types';

export const load = (async ({ parent }) => {
	const { deploymentInfos } = await parent();
	return { deploymentInfos };
}) satisfies PageLoad;
