import { type Module } from './state';

export const setSearchParam = (search: string, key: string, value: string | null | undefined) => {
	const params = new URLSearchParams(search);
	value ? params.set(key, value) : params.delete(key);
	return params.toString();
};

export const buildGlobalNavSearchParam = (
	search: string,
	targetType: string | null | undefined,
	target: string | null | undefined
) => {
	const params = new URLSearchParams(search);
	targetType
		? params.set('global-nav-target-type', targetType)
		: params.delete('global-nav-target-type');
	target ? params.set('global-nav-target', target) : params.delete('global-nav-target');
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
	console.log('search', search);
	console.log('targetType', targetType);
	console.log('target', target);
	console.log('contextType', contextType);
	console.log('contextIdentifier', contextIdentifier);
	console.log('module', module);
	const params = new URLSearchParams(search);
	targetType
		? params.set('global-nav-target-type', targetType)
		: params.delete('global-nav-target-type');
	target ? params.set('global-nav-target', target) : params.delete('global-nav-target');
	contextType
		? params.set('config-selected-module-context-type', contextType)
		: params.delete('config-selected-module-context-type');
	contextIdentifier
		? params.set('config-selected-module-context-identifier', contextIdentifier)
		: params.delete('config-selected-module-context-identifier');
	module
		? params.set('config-selected-module', module.type)
		: params.delete('config-selected-module');
	return params.toString();
};
