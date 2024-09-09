export const nameToIdentifier = (displayName: string): string =>
	// displayName.toLowerCase().replace(/[^a-z0-9]/g, '-');
	{
		// strip string first
		let identifier = displayName.toLowerCase().replace(/[^a-z0-9]/g, '-');
		// remove leading and trailing hyphens
		identifier = identifier.replace(/^-+|-+$/g, '');
		// remove multiple hyphens
		identifier = identifier.replace(/-+/g, '-');
		// prepend with 'device-' if it doesn't start with a letter
		identifier = /^[a-z]/.test(identifier) ? identifier : `device-${identifier}`;
		return identifier;
	};
