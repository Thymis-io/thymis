//import { queryParam } from 'sveltekit-search-params';
import { globalState, type Module } from './state';
import { get } from 'svelte/store';

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

const hasModule = (
	contextType: string | null | undefined,
	contextIdentifier: string | null | undefined,
	moduleType: string | null | undefined
) => {
	if (contextType === 'tag') {
		const tag = get(globalState).tags.find((t) => t.identifier === contextIdentifier);
		return tag?.modules.some((m) => m.type === moduleType);
	} else if (contextType === 'config') {
		const config = get(globalState).configs.find((c) => c.identifier === contextIdentifier);
		return config?.modules.some((m) => m.type === moduleType);
	}
	return false;
};

const setFirstSelectedModule = (
	params: URLSearchParams,
	contextType: string | null | undefined,
	contextIdentifier: string | null | undefined
) => {
	if (contextType === 'tag') {
		const tag = get(globalState).tags.find((t) => t.identifier === contextIdentifier);
		setParam(params, 'config-selected-module', tag?.modules[0]?.type);
	} else if (contextType === 'config') {
		const config = get(globalState).configs.find((c) => c.identifier === contextIdentifier);
		setParam(params, 'config-selected-module', config?.modules[0]?.type);
	}
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
	if (
		!params.get('config-selected-module') ||
		!hasModule(targetType, target, params.get('config-selected-module'))
	) {
		setFirstSelectedModule(params, targetType, target);
	}
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
	if (!module || !hasModule(contextType, contextIdentifier, module.type)) {
		setFirstSelectedModule(params, contextType, contextIdentifier);
	}
	return params.toString();
};

export const configSelectedModuleContextType = undefined; /* queryParam<ContextType>(
	'config-selected-module-context-type'
);*/

export const configSelectedModuleContext = undefined; /* derived(
	[
		configSelectedModuleContextType,
		queryParam('config-selected-module-context-identifier'),
		globalState
	],
	([$contextType, $contextIdentifier, s]) => {
		if ($contextType === 'tag') {
			return getTagByIdentifier(s, $contextIdentifier);
		} else if ($contextType === 'config') {
			return getConfigByIdentifier(s, $contextIdentifier);
		}
	}
);*/
