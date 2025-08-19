import { toast } from '@zerodevx/svelte-toast';
import type { LayoutServerLoad } from './$types';
import { env } from '$env/dynamic/private';
import { redirectToLogin } from '$lib/login';

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
	await redirectToLogin(cookies, url, fetch);
};
