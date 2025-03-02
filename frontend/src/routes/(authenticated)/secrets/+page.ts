import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	const response = await fetch('/api/secrets');
	if (response.ok) {
		const secrets = await response.json();
		return { secrets };
	}
	return {};
}) satisfies PageLoad;
