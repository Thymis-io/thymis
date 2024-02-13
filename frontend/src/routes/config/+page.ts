import { controllerHost, controllerProtocol } from '$lib/api';
import type { Module, State } from '$lib/state';
import type { PageLoad } from './$types';

export const load = (async ({ fetch }) => {
	console.log('loading state');
	const stateResponse = await fetch(`${controllerProtocol}://${controllerHost}/state`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	const state = (await stateResponse.json()) as State;
	const availableModulesResponse = await fetch(
		`${controllerProtocol}://${controllerHost}/available_modules`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		}
	);
	const availableModules = (await availableModulesResponse.json()) as Module[];
	console.log('state loaded');
	return {
		state: state,
		availableModules: availableModules
	};
}) satisfies PageLoad;
