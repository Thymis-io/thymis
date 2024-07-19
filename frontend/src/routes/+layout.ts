import { browser } from '$app/environment';
import '$lib/i18n'; // Import to initialize. Important :)
import { locale, waitLocale } from 'svelte-i18n';
import type { LayoutLoad } from './$types';
import { controllerHost, controllerProtocol } from '$lib/api';
import type { State, Module } from '$lib/state';
import { error } from '@sveltejs/kit';

export const load = (async ({ fetch }) => {
	if (browser) {
		let lang = window.navigator.language;
		// split -
		lang = lang.split('-')[0];
		// check cookie and set value from there
		lang =
			document.cookie
				.split('; ')
				.find((row) => row.startsWith('lang='))
				?.split('=')[1] || lang;
		locale.set(lang);
	}
	await waitLocale();
	const stateResponse = await fetch(`${controllerProtocol}://${controllerHost}/state`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});

	const state = (await stateResponse.json()) as State;
	if (!state) {
		error(500, 'Could not fetch state');
	}

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

	return {
		state: state,
		availableModules: availableModules
	};
}) satisfies LayoutLoad;
