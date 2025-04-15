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
	} else {
		console.log('no session, redirecting to login');
		const authmethod = await fetch('/auth/auth/methods');
		if (authmethod.ok) {
			const methods = await authmethod.json();
			console.log('methods', methods);
			if (!methods.oauth2.basic && methods.oauth2) {
				redirect(307, `/auth/login/oauth2`);
			}
		}
	}
	return {};
}) satisfies PageServerLoad;
