import { browser } from '$app/environment';
import '$lib/i18n'; // Import to initialize. Important :)
import { locale, waitLocale } from 'svelte-i18n';
import type { LayoutLoad } from './$types';
import type { State, Module } from '$lib/state';
import { error, redirect } from '@sveltejs/kit';
import { getAllTasks } from '$lib/taskstatus';
import { fetchWithNotify } from '$lib/fetchWithNotify';

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
		locale.set(lang);
	}
	await waitLocale(lang);

	const stateResponse = await fetchWithNotify(
		`/api/state`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		},
		{},
		fetch
	);

	if (stateResponse.status === 401) {
		redirect(307, '/login?redirect=' + encodeURIComponent(url.pathname + url.search));
	}
	const state = (await stateResponse.json()) as State;
	if (!state) {
		error(500, 'Could not fetch state');
	}

	const availableModulesResponse = await fetchWithNotify(
		`/api/available_modules`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		},
		{
			500: 'Could not fetch available modules'
		},
		fetch
	);

	let availableModules: Module[] = [];

	// const availableModules = (await availableModulesResponse.json()) as Module[];
	try {
		availableModules = (await availableModulesResponse.json()) as Module[];
	} catch (e) {
		console.error('Error fetching available modules', e);
	}

	const taskPage = parseInt(url.searchParams.get('task-page') || '1');
	const tasksPerPage = 20;
	const { tasks: allTasks, totalCount: totalTaskCount } = await getAllTasks(
		tasksPerPage,
		(taskPage - 1) * tasksPerPage,
		fetch
	);
	const minimizeTaskbar = data?.minimizeTaskbar === 'true';
	const vncDisplaysPerColumn = parseInt(data?.vncDisplaysPerColumn || '3');
	const inPlaywright = data?.inPlaywright || false;

	return {
		state: state,
		availableModules: availableModules,
		allTasks: allTasks,
		totalTaskCount: totalTaskCount,
		tasksPerPage: tasksPerPage,
		minimizeTaskbar: minimizeTaskbar,
		vncDisplaysPerColumn: vncDisplaysPerColumn,
		inPlaywright: inPlaywright
	};
}) satisfies LayoutLoad;
