import { goto, invalidate } from '$app/navigation';
import { controllerHost, controllerProtocol } from './api';
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type Module = {
	type: string;
	settings: {
		[key: string]: {
			value: string | number | boolean;
		};
	};
};

export type SettingDefinition = {
	name: string;
	type: string;
	options?: string[];
	default: string;
	description: string;
	example: string | null;
};

export type ModuleDefinition = {
	type: string;
	icon: string;
	displayName: string;
} & Record<string, SettingDefinition>;

export type Tag = {
	displayName: string;
	identifier: string;
	priority: number;
	modules: Module[];
};

export type Device = {
	displayName: string;
	identifier: string;
	targetHost: string;
	modules: Module[];
	tags: string[];
};

export type State = {
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
