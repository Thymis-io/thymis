import type { PageLoad } from './$types';
import { getHostkey, type Hostkey } from '$lib/hostkey';

export const load: PageLoad = async ({ fetch, url }) => {
	let hostkey: Hostkey = null;
	const identifier = url.searchParams.get('global-nav-target');
	if (identifier) {
		hostkey = await getHostkey(fetch, identifier);
	}

	return { hostkey };
};
