import { describe, it, expect } from 'vitest';
import { localeFromCookieString, normalizeLocale, resolveInitialLocale } from './index';

describe('localeFromCookieString', () => {
	it('extracts the locale cookie value', () => {
		expect(localeFromCookieString('locale=de')).toBe('de');
		expect(localeFromCookieString('session-id=abc; locale=de; theme=dark')).toBe('de');
	});

	it('tolerates missing spaces between cookies', () => {
		expect(localeFromCookieString('session-id=abc;locale=de;theme=dark')).toBe('de');
	});

	it('returns undefined when no locale cookie is present', () => {
		expect(localeFromCookieString('')).toBeUndefined();
		expect(localeFromCookieString('session-id=abc; theme=dark')).toBeUndefined();
	});
});

describe('normalizeLocale', () => {
	it('passes through supported locales', () => {
		expect(normalizeLocale('en')).toBe('en');
		expect(normalizeLocale('de')).toBe('de');
	});

	it('clamps unsupported or malicious values to the default locale', () => {
		expect(normalizeLocale('fr')).toBe('en');
		expect(normalizeLocale(undefined)).toBe('en');
		expect(normalizeLocale(null)).toBe('en');
		// XSS payload (interpolated into <html lang> server-side) must not survive.
		expect(normalizeLocale('"><script>alert(1)</script>')).toBe('en');
	});
});

describe('resolveInitialLocale', () => {
	it('clamps an unsupported cookie locale to the default', () => {
		expect(resolveInitialLocale('locale="><script>', 'en-US')).toBe('en');
		expect(resolveInitialLocale('locale=fr', 'en-US')).toBe('en');
	});

	it('prefers the locale cookie over the browser language', () => {
		expect(resolveInitialLocale('locale=de', 'en-US')).toBe('de');
	});

	it('falls back to the browser language when no cookie is set', () => {
		expect(resolveInitialLocale('', 'de-DE')).toBe('de');
	});

	it('falls back to the default locale when nothing is available', () => {
		expect(resolveInitialLocale('', undefined)).toBe('en');
	});
});
