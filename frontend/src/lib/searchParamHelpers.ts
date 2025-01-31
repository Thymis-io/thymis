import { queryParam } from 'sveltekit-search-params';
import {
	getDeviceByIdentifier,
	getTagByIdentifier,
	state,
	type ContextType,
	type Module
} from './state';
import { derived } from 'svelte/store';

const setParam = (params: URLSearchParams, key: string, value: string | null | undefined) => {
	if (value) {
		params.set(key, value);
	} else {
		params.delete(key);
	}
};

export const setSearchParam = (search: string, key: string, value: string | null | undefined) => {
	const params = new URLSearchParams(search);
	setParam(params, key, value);
	return params.toString();
};

export const buildGlobalNavSearchParam = (
	search: string,
	targetType: string | null | undefined,
	target: string | null | undefined
) => {
	const params = new URLSearchParams(search);
	setParam(params, 'global-nav-target-type', targetType);
	setParam(params, 'global-nav-target', target);
	setParam(params, 'config-selected-module-context-type', targetType);
	setParam(params, 'config-selected-module-context-identifier', target);
	return params.toString();
};

export const buildConfigSelectModuleSearchParam = (
	search: string,
	targetType: string | null | undefined,
	target: string | null | undefined,
	contextType: string | null | undefined,
	contextIdentifier: string | null | undefined,
	module: Module | null | undefined
) => {
	const params = new URLSearchParams(search);
	setParam(params, 'global-nav-target-type', targetType);
	setParam(params, 'global-nav-target', target);
	setParam(params, 'config-selected-module-context-type', contextType);
	setParam(params, 'config-selected-module-context-identifier', contextIdentifier);
	setParam(params, 'config-selected-module', module?.type);
	return params.toString();
};

export const configSelectedModuleContextType = queryParam<ContextType>(
	'config-selected-module-context-type'
);

export const configSelectedModuleContext = derived(
	[configSelectedModuleContextType, queryParam('config-selected-module-context-identifier'), state],
	([$contextType, $contextIdentifier, s]) => {
		if ($contextType === 'tag') {
			return getTagByIdentifier(s, $contextIdentifier);
		} else if ($contextType === 'config') {
			return getDeviceByIdentifier(s, $contextIdentifier);
		}
	}
);
