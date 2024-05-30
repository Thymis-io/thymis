import { goto, invalidate } from '$app/navigation';
import { controllerHost, controllerProtocol } from './api';
import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type ModuleSettings = {
	type: string;
	settings: {
		[key: string]: string | number | boolean;
	};
};

export type Setting = {
	name: string;
	type: string;
	options?: string[];
	default: string;
	description: string;
	example: string | null;
};

export type Module = {
	type: string;
	icon: string;
	displayName: string;
	settings: Record<string, Setting>;
};

export type Tag = {
	displayName: string;
	identifier: string;
	priority: number;
	modules: ModuleSettings[];
};

export type Device = {
	displayName: string;
	identifier: string;
	targetHost: string;
	modules: ModuleSettings[];
	tags: string[];
};

export type Repo = {
	url: string;
};

export type State = {
	repositories: { [name: string]: Repo };
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
