import type { Setting } from '#lib/state.js';

/**
 * Settings with `type: 'url'` must be absolute HTTP(S) URLs.
 * Empty values are allowed: they mean "use the default / unset".
 */
export const isValidUrl = (value: unknown): boolean => {
	if (value === undefined || value === null || value === '') {
		return true;
	}
	if (typeof value !== 'string' || /\s/.test(value)) {
		return false;
	}
	try {
		const url = new URL(value);
		return (url.protocol === 'http:' || url.protocol === 'https:') && url.hostname.length > 0;
	} catch {
		return false;
	}
};

export const isValidSettingValue = (setting: Setting, value: unknown): boolean => {
	if (setting.type === 'url') {
		return isValidUrl(value);
	}
	return true;
};
