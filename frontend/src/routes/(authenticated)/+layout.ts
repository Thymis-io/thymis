import { browser } from '$app/environment';
import '$lib/i18n'; // Import to initialize. Important :)
import { locale, waitLocale } from 'svelte-i18n';
import type { LayoutLoad } from './$types';
import type { State, Module } from '$lib/state';
import { error, redirect } from '@sveltejs/kit';
import { getAllTasks } from '$lib/taskstatus';

export const load = (async ({ fetch, url, data }) => {
	let lang = 'en';
	if (browser) {
		lang = window.navigator.language;
		// split -
		lang = lang.split('-')[0];
		// check cookie and set value from there
		lang =
			document.cookie
				.split('; ')
				.find((row) => row.startsWith('locale='))
				?.split('=')[1] || lang;
		console.log('setting locale:', lang);
		locale.set(lang);
	}
	await waitLocale(lang);
	const stateResponse = await fetch(`/api/state`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});

	if (stateResponse.status === 401) {
		redirect(307, '/login?redirect=' + encodeURIComponent(url.pathname));
	}
	const state = (await stateResponse.json()) as State;
	if (!state) {
		error(500, 'Could not fetch state');
	}

	const availableModulesResponse = await fetch(`/api/available_modules`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});

	const availableModules = (await availableModulesResponse.json()) as Module[];

	const allTasks = await getAllTasks(fetch);
	const minimizeTaskbar = data?.minimizeTaskbar === 'true';

	return {
		state: state,
		availableModules: availableModules,
		allTasks: allTasks,
		minimizeTaskbar: minimizeTaskbar
	};
}) satisfies LayoutLoad;
