import { getMyIp } from '$lib/server/native';
import type { PageServerLoad } from './$types';

export const load = (async () => {
	let ip = null;
	try {
		ip = await getMyIp();
	} catch (e) {
		/* empty */
	}
	return { ip };
}) satisfies PageServerLoad;
