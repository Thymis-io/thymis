import type { Setting } from '#lib/state.js';

/** i18n key describing why a setting value was rejected. */
export type SettingValueError = 'config.invalid-url' | 'config.invalid-file-url';

/**
 * Settings with `type: 'url'` must be absolute HTTP(S) URLs or `file://` URLs with an
 * absolute path (e.g. `file:///var/image.png`).
 * Empty values are allowed: they mean "use the default / unset".
 */
export const urlError = (value: unknown): SettingValueError | null => {
	if (value === undefined || value === null || value === '') {
		return null;
	}
	if (typeof value !== 'string' || /\s/.test(value)) {
		return 'config.invalid-url';
	}
	// `new URL` silently repairs inputs like `http:/host`, `http:host`, `http:///host` or
	// `file:/path` into canonical form; the backend (urllib.parse) does not, so require
	// the literal `//` followed by a non-empty authority (or `///` + path for file URLs).
	if (/^file:/i.test(value)) {
		if (!/^file:\/\/\/[^/\\]/i.test(value)) {
			return 'config.invalid-file-url';
		}
		try {
			const url = new URL(value);
			return url.protocol === 'file:' && url.hostname === '' ? null : 'config.invalid-file-url';
		} catch {
			return 'config.invalid-file-url';
		}
	}
	if (!/^https?:\/\/[^/\\]/i.test(value)) {
		return 'config.invalid-url';
	}
	try {
		const url = new URL(value);
		return (url.protocol === 'http:' || url.protocol === 'https:') && url.hostname.length > 0
			? null
			: 'config.invalid-url';
	} catch {
		return 'config.invalid-url';
	}
};

export const settingValueError = (setting: Setting, value: unknown): SettingValueError | null => {
	if (setting.type === 'url') {
		return urlError(value);
	}
	return null;
};
