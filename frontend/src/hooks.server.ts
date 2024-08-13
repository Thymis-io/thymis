import type { Handle, HandleFetch } from '@sveltejs/kit';
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

export const handleFetch: HandleFetch = async ({ request, fetch, event }) => {
	const parsedRequestUrl = new URL(request.url);
	if (event.url.host === parsedRequestUrl.host && parsedRequestUrl.pathname.startsWith('/api')) {
		const session = event.cookies.get('session');
		if (session) {
			const cookies = request.headers.get('cookie') || '';
			request.headers.set('cookie', `${cookies}; session=${session}`);
		}
	}
	return fetch(request);
};
