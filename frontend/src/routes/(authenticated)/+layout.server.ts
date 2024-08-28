import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
	const minimizeTasbar = cookies.get('taskbar-minimized');

	return {
		minimizeTasbar: minimizeTasbar
	};
};
