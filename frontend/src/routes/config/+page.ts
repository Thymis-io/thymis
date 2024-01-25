import type { Module, State } from '$lib/state';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	console.log('loading');
	const stateResponse = await fetch('http://localhost:8000/state', {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	const state = (await stateResponse.json()) as State;
	const availableModulesResponse = await fetch('http://localhost:8000/available_modules', {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	const availableModules = (await availableModulesResponse.json()) as Module[];
	return {
		state: state,
		availableModules: availableModules
	};
}) satisfies PageLoad;
