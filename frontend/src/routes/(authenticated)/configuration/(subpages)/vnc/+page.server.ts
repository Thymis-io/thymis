import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies }) => {
	const rawVncDisplaysPerColumn = cookies.get('vnc-displays-per-column');
	return {
		vncDisplaysPerColumn: rawVncDisplaysPerColumn ? parseInt(rawVncDisplaysPerColumn, 10) || 3 : 3
	};
};
