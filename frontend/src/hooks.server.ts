import type { Handle, HandleFetch } from '@sveltejs/kit';
import '$lib/i18n';
import { locale } from 'svelte-i18n';
import { controllerHost } from '$lib/api';

export const handle: Handle = async ({ event, resolve }) => {
	let lang = event.request.headers.get('accept-language')?.split(',')[0]?.split('-')[0];
	// check for language override cookie
	lang = event.cookies.get('locale') || lang;
	if (lang) {
		locale.set(lang);
	}
	return resolve(event, {
		filterSerializedResponseHeaders: (name) => ['total-count'].includes(name)
	});
};

const cookiesToSend = ['session-id', 'session-token'];

export const handleFetch: HandleFetch = async ({ request, fetch, event }) => {
	const parsedRequestUrl = new URL(request.url);
	if (event.url.host === parsedRequestUrl.host && parsedRequestUrl.pathname.startsWith('/api')) {
		for (const cookie of cookiesToSend) {
			const value = event.cookies.get(cookie);
			if (value) {
				const cookies = request.headers.get('cookie') || '';
				request.headers.set('cookie', `${cookies}; ${cookie}=${value}`);
			}
		}
		const parsedControllerHost = new URL(controllerHost);
		const new_url = request.url.replace(parsedRequestUrl.origin, parsedControllerHost.origin);
		console.log('fetching:', new_url);
		request = new Request(new_url, request);
	}
	return fetch(request);
};
