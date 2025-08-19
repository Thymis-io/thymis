import { redirect, type Cookies } from '@sveltejs/kit';

const createRedirectCookie = (cookies: Cookies, url: URL) => {
	const redirectId = Math.random().toString(36).substring(2, 15) + url.pathname;
	const redirectCookie = cookies.get('login-redirect');
	let redirectCookieDict: Record<string, string> = {};
	if (redirectCookie) {
		redirectCookieDict = JSON.parse(redirectCookie);
	}
	redirectCookieDict[redirectId] = url.pathname + url.search;
	cookies.set('login-redirect', JSON.stringify(redirectCookieDict), {
		httpOnly: true,
		secure: url.protocol === 'https:',
		sameSite: 'strict',
		maxAge: 60 * 60 * 24, // 24 hours
		path: '/'
	});
	return redirectId;
};

export const redirectToLogin = async (
	cookies: Cookies | undefined,
	url: URL | undefined,
	fetch: (input: RequestInfo, init?: RequestInit) => Promise<Response>
) => {
	let redirectId = '';

	if (cookies && url) {
		redirectId = createRedirectCookie(cookies, url);
	}

	const authMethods = await fetch('/auth/auth/methods');
	if (authMethods.ok) {
		const methods = await authMethods.json();
		if (!methods.oauth2.basic && methods.oauth2) {
			if (redirectId) {
				redirect(303, `/auth/login/oauth2?redirect=${redirectId}`);
			} else {
				redirect(303, `/auth/login/oauth2`);
			}
		}
	}

	if (redirectId) {
		redirect(303, `/login?redirect=${redirectId}`);
	} else {
		redirect(303, '/login');
	}
};
