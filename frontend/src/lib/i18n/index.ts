import { browser } from '$app/environment';
import { init, register } from 'svelte-i18n';

const defaultLocale = 'en';

// Allowlist for untrusted locale input (cookie/header).
export const supportedLocales = ['en', 'de'] as const;

register('en', () => import('../../locales/en.json'));
register('de', () => import('../../locales/de.json'));

export const normalizeLocale = (lang: string | undefined | null): string =>
	lang && (supportedLocales as readonly string[]).includes(lang) ? lang : defaultLocale;

export const localeFromCookieString = (cookieString: string): string | undefined =>
	cookieString
		.split(';')
		.map((row) => row.trim())
		.find((row) => row.startsWith('locale='))
		?.slice('locale='.length);

// Cookie takes precedence over browser language so the client matches the server-rendered language.
export const resolveInitialLocale = (
	cookieString: string,
	navigatorLanguage: string | undefined
): string =>
	normalizeLocale(localeFromCookieString(cookieString) || navigatorLanguage?.split('-')[0]);

init({
	fallbackLocale: defaultLocale,
	initialLocale: browser
		? resolveInitialLocale(document.cookie, window.navigator.language)
		: defaultLocale
});
