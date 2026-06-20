import { toast } from '@zerodevx/svelte-toast';
import type { LayoutServerLoad } from './$types';
import { env } from '$env/dynamic/private';
import { redirectToLogin } from '$lib/login';
import { normalizeLocale } from '$lib/i18n';

export const load: LayoutServerLoad = async ({ cookies, fetch, url, request }) => {
	// Pass the resolved locale to the client so it hydrates in the server-rendered language.
	const locale = normalizeLocale(
		cookies.get('locale') || request.headers.get('accept-language')?.split(',')[0]?.split('-')[0]
	);

	const session = cookies.get('session-id');
	if (session) {
		// check for valid session
		const loggedInResponse = await fetch('/auth/logged_in');
		if (loggedInResponse.ok) {
			toast.pop(0);
			const minimizeTaskbar = cookies.get('taskbar-minimized');
			const vncDisplaysPerColumn = cookies.get('vnc-displays-per-column');
			const user = await loggedInResponse.json().catch(() => null);

			return {
				locale: locale,
				minimizeTaskbar: minimizeTaskbar,
				vncDisplaysPerColumn: vncDisplaysPerColumn,
				user: user,
				inPlaywright: 'RUNNING_IN_PLAYWRIGHT' in env && env.RUNNING_IN_PLAYWRIGHT === 'true'
			};
		}
	}
	await redirectToLogin(cookies, url, fetch);
};
