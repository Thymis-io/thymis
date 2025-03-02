import type { Handle, HandleFetch } from '@sveltejs/kit';
import '$lib/i18n';
import { locale } from 'svelte-i18n';
import { env } from '$env/dynamic/private';

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

const DEFAULT_BASE_URL = 'http://127.0.0.1:8000';
let privateBaseUrl = new URL(env.PRIVATE_BASE_URL ? env.PRIVATE_BASE_URL : DEFAULT_BASE_URL);

const validHosts = ['localhost', '127.0.0.1', '::1'];
if (
	!(
		privateBaseUrl.protocol === 'http:' &&
		validHosts.some((host) => privateBaseUrl.host.startsWith(host))
	)
) {
	console.warn(
		`Private base URL host "${privateBaseUrl.host}" is not localhost. This is probably a mistake.`
	);
	console.warn('Using default base URL:', DEFAULT_BASE_URL);
	privateBaseUrl = new URL(DEFAULT_BASE_URL);
}

export const handleFetch: HandleFetch = async ({ request, fetch, event }) => {
	const parsedRequestUrl = new URL(request.url);
	if (
		event.url.host === parsedRequestUrl.host &&
		(parsedRequestUrl.pathname.startsWith('/api') || parsedRequestUrl.pathname.startsWith('/auth'))
	) {
		for (const cookie of cookiesToSend) {
			const value = event.cookies.get(cookie);
			if (value) {
				const cookies = request.headers.get('cookie') || '';
				request.headers.set('cookie', `${cookies}; ${cookie}=${value}`);
			}
		}

		const new_url = new URL(request.url);
		new_url.host = privateBaseUrl.host;
		new_url.protocol = privateBaseUrl.protocol;

		request = new Request(new_url, request);
	}
	return fetch(request);
};
