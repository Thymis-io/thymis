import type { PageLoad } from './$types';
import type { State } from '$lib/state';
import { controllerHost, controllerProtocol } from '$lib/api';

export const load = (async ({ fetch }) => {
	const stateResponse = await fetch(`${controllerProtocol}://${controllerHost}/state`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});

	const state = (await stateResponse.json()) as State;

	return {
		state: state
	};
}) satisfies PageLoad;
