import { browser } from '$app/environment';
import '$lib/i18n'; // Import to initialize. Important :)
import { locale, waitLocale } from 'svelte-i18n';
import type { LayoutLoad } from './$types';
import {
	type State,
	type Module,
	type ContextType,
	type Config,
	type Tag,
	getTagByIdentifier,
	getConfigByIdentifier
} from '$lib/state';
import { error, redirect } from '@sveltejs/kit';
import { getAllTasks } from '$lib/taskstatus';
import { fetchWithNotify } from '$lib/fetchWithNotify';
import { type RepoStatus } from '$lib/repo/repo';
import { GlobalState } from '$lib/state.svelte';

export type Nav = {
	selectedTargetType: ContextType | null;
	selectedTargetIdentifier: string | null;
	selectedConfig: Config | undefined;
	selectedTag: Tag | undefined;
	selectedTarget: Config | Tag | undefined;
	selectedModule: Module | undefined;
	selectedModuleContext: Config | Tag | undefined;
	selectedModuleContextType: ContextType | null;
	selectedModuleContextIdentifier: string | null;
};

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

	const selectedTargetType = url.searchParams.get('global-nav-target-type') as ContextType;
	const selectedTargetIdentifier = url.searchParams.get('global-nav-target');
	const selectedConfig =
		selectedTargetType === 'config'
			? getConfigByIdentifier(globalState, selectedTargetIdentifier)
			: undefined;
	const selectedTag =
		selectedTargetType === 'tag'
			? getTagByIdentifier(globalState, selectedTargetIdentifier)
			: undefined;
	const selectedTarget = selectedConfig || selectedTag;

	const configSelectedModule = url.searchParams.get('config-selected-module');
	const selectedModule = availableModules.find((module) => module.type === configSelectedModule);
	const selectedModuleContextType = url.searchParams.get(
		'config-selected-module-context-type'
	) as ContextType;
	const selectedModuleContextIdentifier = url.searchParams.get(
		'config-selected-module-context-identifier'
	);
	const selectedModuleContextConfig =
		selectedModuleContextType === 'config'
			? getConfigByIdentifier(globalState, selectedModuleContextIdentifier)
			: undefined;
	const selectedModuleContextTag =
		selectedModuleContextType === 'tag'
			? getTagByIdentifier(globalState, selectedModuleContextIdentifier)
			: undefined;
	const selectedModuleContext = selectedModuleContextConfig || selectedModuleContextTag;

	const nav: Nav = {
		selectedTargetType,
		selectedTargetIdentifier,
		selectedConfig,
		selectedTag,
		selectedTarget,
		selectedModule,
		selectedModuleContext,
		selectedModuleContextType,
		selectedModuleContextIdentifier
	};

	return {
		globalState: globalState,
		classState: new GlobalState(globalState, url.searchParams, availableModules),
		secrets: secrets,
		nav: nav,
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
