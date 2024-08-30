import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
	const minimizeTaskbar = cookies.get('taskbar-minimized');

	return {
		minimizeTaskbar: minimizeTaskbar
	};
};
