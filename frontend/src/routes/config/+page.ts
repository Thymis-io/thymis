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

export const load = (async () => {
	const response = await fetch('http://0.0.0.0:8000/state', {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});
	// return {
	//     state: response.json() as Promise<State>
	// };
	const state = (await response.json()) as State;
	console.log(state);
	return {
		state: state
	};
}) satisfies PageLoad;
