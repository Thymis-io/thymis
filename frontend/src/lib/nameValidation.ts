import { t } from 'svelte-i18n';
import { get } from 'svelte/store';
import { state } from '$lib/state';

export const nameToIdentifier = (displayName: string): string => {
	// strip string first
	let identifier = displayName.toLowerCase().replace(/[^a-z0-9]/g, '-');
	// remove leading and trailing hyphens
	identifier = identifier.replace(/^-+|-+$/g, '');
	// remove multiple hyphens
	identifier = identifier.replace(/-+/g, '-');
	// prepend with 'config-' if it doesn't start with a letter
	identifier = /^[a-z]/.test(identifier) ? identifier : `config-${identifier}`;

	return identifier;
};

export const nameValidation = (displayName: string, targetType: string): string | undefined => {
	if (displayName.length === 0) {
		return get(t)('create-configuration.display-name-cannot-be-empty');
	}

	const identifier = nameToIdentifier(displayName);

	if (targetType === 'config') {
		if (get(state).configs.find((config) => config.displayName === displayName)) {
			return get(t)('create-configuration.device-with-display-name-name-exists', {
				values: { displayName }
			});
		}

		if (get(state).configs.find((config) => config.identifier === identifier)) {
			return get(t)('create-configuration.identifier-exists');
		}
	} else if (targetType === 'tag') {
		if (get(state).tags.find((tag) => tag.displayName === displayName)) {
			return get(t)('create-configuration.tag-with-display-name-name-exists', {
				values: { displayName }
			});
		}

		if (get(state).tags.find((tag) => tag.identifier === identifier)) {
			return get(t)('create-configuration.identifier-exists');
		}
	}
};

export const deviceTypeValidation = (deviceType: string | undefined): string | undefined => {
	if (!deviceType) return get(t)('create-configuration.device-type-cannot-be-empty');
};
