import { goto, invalidate } from '$app/navigation';
import { controllerHost, controllerProtocol } from './api';
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type SettingTypes =
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
	}
	| {
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

export const build = async () => {
	await fetch(`${controllerProtocol}://${controllerHost}/action/build`, { method: 'POST' });
};

export async function saveState(state: State) {
	await fetch(`${controllerProtocol}://${controllerHost}/state`, {
		method: 'PATCH',
		headers: {
			'content-type': 'application/json'
		},
		body: JSON.stringify(state)
	});
	await invalidate((url) => url.pathname === '/state' || url.pathname === '/available_modules');
	await build();
}
