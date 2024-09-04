import { type Module } from './state';

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
