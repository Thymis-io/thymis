import { describe, it, expect } from 'vitest';
import { settingValueError, urlError } from './settingValidation';
import type { Setting } from '#lib/state.js';

const urlSetting: Setting = { displayName: 'URL', type: 'url' };
const stringSetting: Setting = { displayName: 'Text', type: 'string' };

describe('urlError', () => {
	it('accepts absolute http(s) and file URLs', () => {
		expect(urlError('https://thymis.example.com')).toBeNull();
		expect(urlError('http://localhost:8000')).toBeNull();
		expect(urlError('https://example.com/base/path?query=1')).toBeNull();
		expect(urlError('http://[::1]:8080')).toBeNull();
		expect(urlError('file:///var/image.png')).toBeNull();
	});

	it('accepts empty values as unset', () => {
		expect(urlError('')).toBeNull();
		expect(urlError(undefined)).toBeNull();
		expect(urlError(null)).toBeNull();
	});

	it('rejects values that are not absolute http(s) URLs', () => {
		for (const value of [
			'example.com',
			'ftp://example.com',
			'https://',
			'https://example.com:99999',
			'https://exa mple.com',
			42,
			'http:/123',
			'http:example.com',
			'http:\\\\example.com',
			'http:///path'
		]) {
			expect(urlError(value)).toBe('config.invalid-url');
		}
	});

	it('explains file URLs without an absolute path', () => {
		for (const value of [
			'file://var/image.png',
			'file:/var/image.png',
			'file://host/var/image.png',
			'file:///'
		]) {
			expect(urlError(value)).toBe('config.invalid-file-url');
		}
	});
});

describe('settingValueError', () => {
	it('validates url settings', () => {
		expect(settingValueError(urlSetting, 'https://thymis.example.com')).toBeNull();
		expect(settingValueError(urlSetting, 'not a url')).toBe('config.invalid-url');
	});

	it('leaves other setting types alone', () => {
		expect(settingValueError(stringSetting, 'not a url')).toBeNull();
	});
});
