import { controllerHost, controllerProtocol } from '$lib/api';
import type { Module, State } from '$lib/state';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load = (async ({ fetch, url }) => {
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
	// check query params
	// if tag and device are not set, redirect to first device

	const queryParams = new URLSearchParams(url.search);
	const tag = queryParams.get('tag');
	const device = queryParams.get('device');

	if (!tag && !device) {
		const firstDevice = state.devices[0];
		if (firstDevice) {
			redirect(300, `/config?&device=${firstDevice.hostname}`);
		}
	}

	return {
		state: state,
		availableModules: availableModules
	};
}) satisfies PageLoad;
