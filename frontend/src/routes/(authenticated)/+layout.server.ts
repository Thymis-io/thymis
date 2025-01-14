import { toast } from '@zerodevx/svelte-toast';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
	toast.pop(0);
	const minimizeTaskbar = cookies.get('taskbar-minimized');

	return {
		minimizeTaskbar: minimizeTaskbar
	};
};
