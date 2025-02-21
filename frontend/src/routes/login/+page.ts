import '$lib/i18n'; // Import to initialize. Important :)
import { locale, waitLocale } from 'svelte-i18n';
import type { PageLoad } from './$types';
import { browser } from '$app/environment';

export const load = (async () => {
	let lang = 'en';
	if (browser) {
		lang = window.navigator.language;
		// split -
		lang = lang.split('-')[0];
		// check cookie and set value from there
		lang =
			document.cookie
				.split('; ')
				.find((row) => row.startsWith('locale='))
				?.split('=')[1] || lang;
		locale.set(lang);
	}
	await waitLocale(lang);
	return {};
}) satisfies PageLoad;
