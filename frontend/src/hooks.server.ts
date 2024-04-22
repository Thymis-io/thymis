import type { Handle } from '@sveltejs/kit';
import { locale } from 'svelte-i18n';

export const handle: Handle = async ({ event, resolve }) => {
	let lang = event.request.headers.get('accept-language')?.split(',')[0]?.split('-')[0];
	// check for language override cookie
	lang = event.cookies.get('lang') || lang;
	if (lang) {
		locale.set(lang);
	}
	return resolve(event);
};
