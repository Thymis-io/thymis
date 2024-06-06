import type { Module, State } from './state';
import { page } from '$app/stores';
import { queryParam } from 'sveltekit-search-params';
import { derived } from 'svelte/store';

export const deviceUrl = (search: string, context: string, identifier: string) => {
	const params = new URLSearchParams(search);
	params.set('id-context', context);
	params.set('id', identifier);
	return params.toString();
};

export const deviceConfigUrl = (
	search: string,
	module: Module,
	context: string,
	identifier: string
) => {
	const params = new URLSearchParams(search);
	params.set('config-id-context', context);
	params.set('config-id', identifier);
	params.set('module', module.type);
	return params.toString();
};

export const selectedTag = derived(
	[page, queryParam('id-context'), queryParam('id')],
	([$page, $context, $identifier]) => {
		let state = $page.data.state as State;

		if ($context === 'tag') {
			return state.tags.find((tag) => tag.identifier === $identifier);
		}
	}
);

export const selectedDevice = derived(
	[page, queryParam('id-context'), queryParam('id')],
	([$page, $context, $identifier]) => {
		let state = $page.data.state as State;

		if ($context === 'device') {
			return state.devices.find((device) => device.identifier === $identifier);
		}
	}
);

export const selectedTarget = derived(
	[selectedDevice, selectedTag],
	([$device, $tag]) => $device || $tag
);

export const selectedContext = derived(queryParam('id-context'), ($context) => $context);

export const selectedConfigTarget = derived(
	[page, queryParam('config-id-context'), queryParam('config-id')],
	([$page, $context, $identifier]) => {
		let state = $page.data.state as State;

		if ($context === 'tag') {
			return state.tags.find((tag) => tag.identifier === $identifier);
		} else if ($context === 'device') {
			return state.devices.find((device) => device.identifier === $identifier);
		}
	}
);

export const selectedConfigContext = derived(
	queryParam('config-id-context'),
	($context) => $context
);

export const selectedConfigModule = derived([page, queryParam('module')], ([$page, $module]) => {
	let availableModules = $page.data.availableModules as Module[];
	return availableModules.find((module) => module.type === $module);
});
