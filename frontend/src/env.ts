import { defineEnvVars } from '@sveltejs/kit/env';

// @migration-task Review usage of dynamic environment variables. They fall back to the empty string if not present, which may not be what you want.
export const variables = defineEnvVars({
	PRIVATE_BASE_URL: { schema: (input) => input ?? '' },
	RUNNING_IN_PLAYWRIGHT: { schema: (input) => input ?? '' }
});
