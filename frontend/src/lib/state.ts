import { invalidate } from '$app/navigation';
import { writable } from 'svelte/store';
import { fetchWithNotify } from './fetchWithNotify';

export type ModuleSettings = {
	type: string;
	settings: {
		[key: string]: unknown;
	};
};

export type Origin = {
	originId: string;
	originContext: string;
	originName: string;
};

export type ModuleSettingsWithOrigin = {
	type: string;
	settings: {
		[key: string]: unknown;
	};
	originId: string;
	originContext: string;
	originName: string;
	priority: number | undefined;
};

export type SelectOneSettingType = {
	'select-one': string[][];
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	extra_data?: Record<string, any>;
};

export type ListSettingType = {
	'list-of': Setting[];
	'element-name': string | undefined;
};

export type SettingType =
	| 'string'
	| 'number'
	| 'bool'
	| 'textarea'
	| 'int'
	| SelectOneSettingType
	| ListSettingType;

export type Setting<T extends SettingType = SettingType> = {
	displayName: string;
	type: T;
	default: string;
	description: string;
	example: string | null;
	order: number;
};

export type Module = {
	type: string;
	icon: string | undefined;
	iconDark: string | undefined;
	displayName: string;
	settings: Record<string, Setting>;
};

export type Tag = {
	displayName: string;
	identifier: string;
	priority: number;
	modules: ModuleSettings[];
};

export type Config = {
	displayName: string;
	identifier: string;
	modules: ModuleSettings[];
	tags: string[];
};

export type Repo = {
	url: string;
};

export type State = {
	repositories: { [name: string]: Repo };
	configs: Config[];
	tags: Tag[];
};

export const globalState = writable<State>();

export let currentState: State;

globalState.subscribe((value) => {
	currentState = value;
});

export const saveState = async () => {
	globalState.set(currentState);
	const response = await fetchWithNotify(`/api/state`, {
		method: 'PATCH',
		headers: {
			'content-type': 'application/json'
		},
		body: JSON.stringify(currentState)
	});
	await invalidate((url) => url.pathname === '/api/state');
	return response.ok;
};

export const build = async () => {
	await fetchWithNotify(`/api/action/build`, { method: 'POST' });
};

export const getTagByIdentifier = (state: State, identifier: string | null) => {
	if (!identifier) return undefined;
	return state.tags.find((tag) => tag.identifier === identifier);
};

export const getConfigByIdentifier = (state: State, identifier: string | null) => {
	if (!identifier) return undefined;
	return state.configs.find((config) => config.identifier === identifier);
};

export type ContextType = 'tag' | 'config';
