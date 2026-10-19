import { defineEnvVars } from '@sveltejs/kit/env';

export const variables = defineEnvVars({
	PRIVATE_BASE_URL: { schema: (input) => input ?? '' },
	RUNNING_IN_PLAYWRIGHT: { schema: (input) => input ?? '' }
});
