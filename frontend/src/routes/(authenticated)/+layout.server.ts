import { toast } from '@zerodevx/svelte-toast';
import type { LayoutServerLoad } from './$types';
import { env } from '$env/dynamic/private';

export const load: LayoutServerLoad = async ({ cookies }) => {
	toast.pop(0);
	const minimizeTaskbar = cookies.get('taskbar-minimized');
	const vncDisplaysPerColumn = cookies.get('vnc-displays-per-column');

	return {
		minimizeTaskbar: minimizeTaskbar,
		vncDisplaysPerColumn: vncDisplaysPerColumn,
		inPlaywright: 'RUNNING_IN_PLAYWRIGHT' in env && env.RUNNING_IN_PLAYWRIGHT === 'true'
	};
};
