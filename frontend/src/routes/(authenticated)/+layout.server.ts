import { toast } from '@zerodevx/svelte-toast';
import type { LayoutServerLoad } from './$types';
import { env } from '$env/dynamic/private';
import { redirect } from '@sveltejs/kit';

export const load: LayoutServerLoad = async ({ cookies, fetch, url }) => {
	const session = cookies.get('session-id');
	if (session) {
		// check for valid session
		const loggedInResponse = await fetch('/auth/logged_in');
		if (loggedInResponse.ok) {
			toast.pop(0);
			const minimizeTaskbar = cookies.get('taskbar-minimized');
			const vncDisplaysPerColumn = cookies.get('vnc-displays-per-column');

			return {
				minimizeTaskbar: minimizeTaskbar,
				vncDisplaysPerColumn: vncDisplaysPerColumn,
				inPlaywright: 'RUNNING_IN_PLAYWRIGHT' in env && env.RUNNING_IN_PLAYWRIGHT === 'true'
			};
		}
	}
	// add redirect cookie
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
	redirect(303, '/login?redirect=' + redirectId);
};
