import { goto, invalidate } from '$app/navigation';
import { controllerHost, controllerProtocol } from './api';
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type SettingTypes =
	{
		type: 'bool';
		value: boolean;
	} | {
		type: 'string';
		value: string;
	} | {
		type: 'path';
		value: string;
	} | {
		type: 'textarea';
		value: string;
	};

export type Setting = SettingTypes & {
	name: string;
	// value: unknown;
	default: string;
	description: string;
	example: string | null;
	// type: string;
};

export type Module = { type: string; name: string } & Record<string, Setting>;

export type SettingValue = { value: SettingTypes };
export type ModuleSettings = { type: string; settings: { [key: string]: SettingValue } };
export type Tag = {
	name: string;
	priority: number;
	modules: (ModuleSettings & { priority: number })[];
};
export type Device = {
	hostname: string;
	displayName: string;
	modules: ModuleSettings[];
	tags: string[];
};

export type State = {
	modules: Module[];
	devices: Device[];
	tags: Tag[];
};

export let state = writable<State | undefined>();
export let availableModules = writable<Module[] | undefined>();

export async function saveState(state: State) {
	await fetch(`${controllerProtocol}://${controllerHost}/state`, {
		method: 'PATCH',
		headers: {
			'content-type': 'application/json'
		},
		body: JSON.stringify(state)
	});
	await invalidate((url) => url.pathname === '/state' || url.pathname === '/available_modules');
}

const load = (async () => {
	console.log('loading state');
	const stateResponse = await fetch(`${controllerProtocol}://${controllerHost}/state`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});

	const loadedState = await stateResponse.json();
	state.set(loadedState)
	const availableModulesResponse = await fetch(`${controllerProtocol}://${controllerHost}/available_modules`, {
		method: 'GET',
		headers: {
			'content-type': 'application/json'
		}
	});

	availableModules.set(await availableModulesResponse.json());
	console.log('state loaded');
	// check query params
	// if tag and device are not set, redirect to first device

	const url = new URL(window.location.href);
	const queryParams = new URLSearchParams(url.search);
	const tag = queryParams.get('tag');
	const device = queryParams.get('device');

	if (!tag && !device) {
		const firstDevice = loadedState.devices[0];
		if (firstDevice) {
			// redirect(300, `?&device=${firstDevice.hostname}`);
			goto(url.pathname + `?&device=${firstDevice.hostname}`);
		}
	}
});

if (browser) {
	load();
}
