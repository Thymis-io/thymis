import type { PageLoad } from './$types';

type SettingTypes =
	| {
		type: 'bool';
		value: boolean;
	}
	| {
		type: 'string';
		value: string;
	}
	| {
		type: 'path';
		value: string;
	};

type Setting = SettingTypes & {
	name: string;
	// value: unknown;
	default: string;
	description: string;
	example: string | null;
	// type: string;
};

type Module = { name: string } & Record<string, Setting>;

type State = {
	modules: Module[];
};

export const load = (async ({ fetch }) => {
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
	// console.log(state);
	return {
		state: state,
		availableModules: availableModules
	};
}) satisfies PageLoad;
