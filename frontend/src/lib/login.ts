import { redirect, type Cookies } from '@sveltejs/kit';

const createRedirectCookie = (cookies: Cookies, url: URL) => {
	const redirectKey = Math.random().toString(36).substring(2, 15);
	const redirectUrl = url.pathname + url.search;
	cookies.set('login-redirect', redirectKey + '-' + redirectUrl, {
		httpOnly: true,
		secure: url.protocol === 'https:',
		sameSite: 'strict',
		maxAge: 60 * 60, // 1 hour
		path: '/'
	});
	return redirectKey;
};

export const redirectToLogin = async (
	cookies: Cookies | undefined,
	url: URL | undefined,
	fetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>
) => {
	let redirectKey = '';

	if (cookies && url) {
		redirectKey = createRedirectCookie(cookies, url);
	}

	const authMethods = await fetch('/auth/auth/methods');
	if (authMethods.ok) {
		const methods = await authMethods.json();
		if (!methods.oauth2.basic && methods.oauth2) {
			if (redirectKey) {
				redirect(303, `/auth/login/oauth2?redirect=${redirectKey}`);
			} else {
				redirect(303, `/auth/login/oauth2`);
			}
		}
	}

	if (redirectKey) {
		redirect(303, `/login?redirect=${redirectKey}`);
	} else {
		redirect(303, '/login');
	}
};
