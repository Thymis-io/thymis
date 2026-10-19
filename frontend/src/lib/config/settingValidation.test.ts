import { describe, it, expect } from 'vitest';
import { isValidSettingValue, isValidUrl } from './settingValidation';
import type { Setting } from '#lib/state.js';

const urlSetting: Setting = { displayName: 'URL', type: 'url' };
const stringSetting: Setting = { displayName: 'Text', type: 'string' };

describe('isValidUrl', () => {
	it('accepts absolute http(s) URLs', () => {
		expect(isValidUrl('https://thymis.example.com')).toBe(true);
		expect(isValidUrl('http://localhost:8000')).toBe(true);
		expect(isValidUrl('https://example.com/base/path?query=1')).toBe(true);
		expect(isValidUrl('http://[::1]:8080')).toBe(true);
	});

	it('accepts empty values as unset', () => {
		expect(isValidUrl('')).toBe(true);
		expect(isValidUrl(undefined)).toBe(true);
		expect(isValidUrl(null)).toBe(true);
	});

	it('rejects values that are not absolute http(s) URLs', () => {
		expect(isValidUrl('example.com')).toBe(false);
		expect(isValidUrl('ftp://example.com')).toBe(false);
		expect(isValidUrl('https://')).toBe(false);
		expect(isValidUrl('https://example.com:99999')).toBe(false);
		expect(isValidUrl('https://exa mple.com')).toBe(false);
		expect(isValidUrl(42)).toBe(false);
	});
});

describe('isValidSettingValue', () => {
	it('validates url settings', () => {
		expect(isValidSettingValue(urlSetting, 'https://thymis.example.com')).toBe(true);
		expect(isValidSettingValue(urlSetting, 'not a url')).toBe(false);
	});

	it('leaves other setting types alone', () => {
		expect(isValidSettingValue(stringSetting, 'not a url')).toBe(true);
	});
});
