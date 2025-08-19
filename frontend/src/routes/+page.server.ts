import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import '$lib/i18n'; // Import to initialize. Important :)
import { redirectToLogin } from '$lib/login';

export const load = (async ({ fetch, cookies, url }) => {
	const session = cookies.get('session-id');
	if (!session) {
		await redirectToLogin(cookies, url, fetch);
	} else {
		redirect(303, '/overview');
	}
	return {};
}) satisfies PageServerLoad;
