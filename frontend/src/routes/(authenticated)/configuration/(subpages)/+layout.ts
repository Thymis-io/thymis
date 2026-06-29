import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';

export const load: LayoutLoad = async ({ url }) => {
	const identifier = url.searchParams.get('global-nav-target');
	const identifierType = url.searchParams.get('global-nav-target-type');
	if (!identifier || !identifierType || (identifierType !== 'config' && identifierType !== 'tag')) {
		redirect(303, '/overview?error-message=No%20config%20id%20provided');
	}
};
