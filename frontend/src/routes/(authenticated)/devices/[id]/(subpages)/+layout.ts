import type { LayoutLoad } from './$types';
import { error } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ params, parent }) => {
	const { globalState } = await parent();
	if (!globalState.deploymentInfos.find((di) => di.id === params.id)) {
		error(404, 'Device not found');
	}
	return { deploymentInfoId: params.id };
};
