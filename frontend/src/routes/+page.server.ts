import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import '$lib/i18n'; // Import to initialize. Important :)

export const load = (async ({ cookies }) => {
	const session = cookies.get('session-id');
	if (!session) {
		redirect(307, '/login');
	} else {
		redirect(303, '/overview');
	}
	return {};
}) satisfies PageServerLoad;
