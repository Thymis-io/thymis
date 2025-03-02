import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load = (async ({ cookies, url, fetch }) => {
	const session = cookies.get('session-id');
	const redirectParam = url.searchParams.get('redirect');
	const redirectCookie = cookies.get('login-redirect');
	if (session) {
		// check for valid session
		const stateResponse = await fetch('/auth/logged_in');
		if (stateResponse.ok) {
			// now, check if there is a redirect cookie
			let redirectUrl = '/overview'; // default redirect
			// check for redirectParam in cookie to preven open redirect
			if (redirectParam && redirectCookie) {
				const redirectCookieDict = JSON.parse(redirectCookie);
				if (redirectCookieDict[redirectParam]) {
					redirectUrl = redirectCookieDict[redirectParam];
				}
			}
			redirect(303, redirectUrl);
		}
	}
	return {};
}) satisfies PageServerLoad;
