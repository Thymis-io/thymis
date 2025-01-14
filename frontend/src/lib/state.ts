import { invalidate } from '$app/navigation';
import { derived, writable } from 'svelte/store';
import { queryParam } from 'sveltekit-search-params';
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

export const state = writable<State>();

let currentState: State;

state.subscribe((value) => {
	currentState = value;
});

export const saveState = async () => {
	state.set(currentState);
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

export const getTagByIdentifier = (state: State, identifier: string) => {
	return state.tags.find((tag) => tag.identifier === identifier);
};

export const getDeviceByIdentifier = (state: State, identifier: string) => {
	return state.devices.find((config) => config.identifier === identifier);
};

export const globalNavSelectedTag = derived(
	[state, queryParam('global-nav-target-type'), queryParam('global-nav-target')],
	([$state, $context, $identifier]) => {
		if ($context === 'tag') {
			return getTagByIdentifier($state, $identifier);
		}
	}
);

export const globalNavSelectedConfig = derived(
	[state, queryParam('global-nav-target-type'), queryParam('global-nav-target')],
	([$state, $context, $identifier]) => {
		if ($context === 'config') {
			return getDeviceByIdentifier($state, $identifier);
		}
	}
);

export const globalNavSelectedTarget = derived(
	[globalNavSelectedConfig, globalNavSelectedTag],
	([$globalNavSelectedConfig, $globalNavSelectedTag]) =>
		$globalNavSelectedConfig || $globalNavSelectedTag
);

export const globalNavSelectedTargetType = queryParam('global-nav-target-type');
