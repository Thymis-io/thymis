import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies }) => {
	const session = cookies.get('session');
	if (!session) {
		redirect(307, '/login');
	}
	else {
		redirect(303, '/overview');
	}
};