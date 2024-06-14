import type { Module, State } from './state';
import { page } from '$app/stores';
import { queryParam } from 'sveltekit-search-params';
import { derived } from 'svelte/store';

export const deviceUrl = (
	search: string,
	context: string | null | undefined,
	identifier: string | null | undefined
) => {
	const params = new URLSearchParams(search);
	context ? params.set('id-context', context) : params.delete('id-context');
	identifier ? params.set('id', identifier) : params.delete('id');
	params.delete('config-id');
	params.delete('config-id-context');
	params.delete('module');
	return params.toString();
};

export const deviceConfigUrl = (
	search: string,
	module: Module | null | undefined,
	context: string | null | undefined,
	identifier: string | null | undefined,
	configContext: string | null | undefined,
	configIdentifier: string | null | undefined
) => {
	const params = new URLSearchParams(search);
	context ? params.set('id-context', context) : params.delete('id-context');
	identifier ? params.set('id', identifier) : params.delete('id');
	configContext
		? params.set('config-id-context', configContext)
		: params.delete('config-id-context');
	configIdentifier ? params.set('config-id', configIdentifier) : params.delete('config-id');
	module ? params.set('module', module.type) : params.delete('module');
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
