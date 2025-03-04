import { browser } from '$app/environment';
import '$lib/i18n'; // Import to initialize. Important :)
import { locale, waitLocale } from 'svelte-i18n';
import type { LayoutLoad } from './$types';
import type { State, Module } from '$lib/state';
import { error, redirect } from '@sveltejs/kit';
import { getAllTasks } from '$lib/taskstatus';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import { type RepoStatus } from '$lib/repo/repo';

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
		redirect(307, '/login');
	}
	if (stateResponse.status === 422) {
		// log
		console.debug('State response status 422');
		console.debug(stateResponse);
		console.debug(await stateResponse.text());
	}
	const globalState = (await stateResponse.json()) as State;
	if (!globalState) {
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

	const repoStatusResponse = await fetchWithNotify(
		`/api/repo_status`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		},
		{},
		fetch
	);

	let repoStatus: RepoStatus = { changes: [] };

	try {
		repoStatus = (await repoStatusResponse.json()) as RepoStatus;
	} catch (e) {
		console.error('Error fetching repo status', e);
	}

	// get secrets
	const secretsResponse = await fetchWithNotify(
		`/api/secrets`,
		{
			method: 'GET',
			headers: {
				'content-type': 'application/json'
			}
		},
		{},
		fetch
	);
	if (secretsResponse.status === 401) {
		redirect(307, '/login');
	}

	// is uuid -> secret
	const secrets = (await secretsResponse.json()) as Record<string, unknown>;

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
		globalState: globalState,
		secrets: secrets,
		availableModules: availableModules,
		repoStatus: repoStatus,
		allTasks: allTasks,
		totalTaskCount: totalTaskCount,
		tasksPerPage: tasksPerPage,
		minimizeTaskbar: minimizeTaskbar,
		vncDisplaysPerColumn: vncDisplaysPerColumn,
		inPlaywright: inPlaywright
	};
}) satisfies LayoutLoad;
