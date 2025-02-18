import { toast } from '@zerodevx/svelte-toast';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
	toast.pop(0);
	const minimizeTaskbar = cookies.get('taskbar-minimized');
	const vncDisplaysPerColumn = cookies.get('vnc-displays-per-column');

	return {
		minimizeTaskbar: minimizeTaskbar,
		vncDisplaysPerColumn: vncDisplaysPerColumn
	};
};
