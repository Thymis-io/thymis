import { invalidate } from '$app/navigation';
import { derived, writable } from 'svelte/store';
import { queryParam } from 'sveltekit-search-params';

export type ModuleSettings = {
	type: string;
	settings: {
		[key: string]: string | number | boolean;
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
		[key: string]: string | number | boolean;
	};
	originId: string;
	originContext: string;
	originName: string;
	priority: number | undefined;
};

export type Setting = {
	name: string;
	type: string;
	options?: string[];
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

export const state = writable<State>();

let currentState: State;

state.subscribe((value) => {
	currentState = value;
});

export const saveState = async () => {
	state.set(currentState);
	await fetch(`/api/state`, {
		method: 'PATCH',
		headers: {
			'content-type': 'application/json'
		},
		body: JSON.stringify(currentState)
	});
	await invalidate((url) => url.pathname === '/api/state');
	await build();
};

export const build = async () => {
	await fetch(`/api/action/build`, { method: 'POST' });
};

export const getTagByIdentifier = (state: State, identifier: string) => {
	return state.tags.find((tag) => tag.identifier === identifier);
};

export const getDeviceByIdentifier = (state: State, identifier: string) => {
	return state.devices.find((device) => device.identifier === identifier);
};

export const globalNavSelectedTag = derived(
	[state, queryParam('global-nav-target-type'), queryParam('global-nav-target')],
	([$state, $context, $identifier]) => {
		if ($context === 'tag') {
			return getTagByIdentifier($state, $identifier);
		}
	}
);

export const globalNavSelectedDevice = derived(
	[state, queryParam('global-nav-target-type'), queryParam('global-nav-target')],
	([$state, $context, $identifier]) => {
		if ($context === 'device') {
			return getDeviceByIdentifier($state, $identifier);
		}
	}
);

export const globalNavSelectedTarget = derived(
	[globalNavSelectedDevice, globalNavSelectedTag],
	([$globalNavSelectedDevice, $globalNavSelectedTag]) =>
		$globalNavSelectedDevice || $globalNavSelectedTag
);

export const globalNavSelectedTargetType = queryParam('global-nav-target-type');
