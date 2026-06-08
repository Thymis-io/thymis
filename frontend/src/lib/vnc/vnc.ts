import type { Config, Module, ModuleSettings, State, Tag } from '$lib/state';

const isVNCModule = (module: ModuleSettings | Module | undefined) => {
	return (
		module?.type === 'thymis_controller.modules.kiosk.Kiosk' ||
		module?.type.toLowerCase().includes('vnc')
	);
};

const tagHasVNCStringModule = (tag: Tag, state: State) => tag.modules.some(isVNCModule);

const configHasEnabledVNC = (config: Config, state: State) => {
	const vncModuleSettings =
		config.modules.find(isVNCModule) ||
		config.tags
			.flatMap((tag) => state.tags.find((t) => t.identifier === tag)?.modules)
			.find(isVNCModule);
	if (vncModuleSettings) {
		return 'enable_vnc' in vncModuleSettings.settings
			? vncModuleSettings.settings.enable_vnc
			: false;
	}
	return false;
};

const customModuleHasVncString = (module: ModuleSettings) => {
	if (!(module.type === 'thymis_controller.modules.whatever.WhateverModule')) return false;
	return JSON.stringify(module).toLowerCase().includes('vnc');
};

const tagHasCustomVNCModule = (tag: Tag, state: State) =>
	tag.modules.some(customModuleHasVncString);

const configHasCustomVNCModule = (config: Config, state: State) =>
	config.modules.some(customModuleHasVncString) ||
	config.tags.some((tag) => {
		const tagObj = state.tags.find((t) => t.identifier === tag);
		if (!tagObj) return false;
		return tagHasCustomVNCModule(tagObj, state);
	});

export const targetShouldShowVNC = (target: Config | Tag | undefined, state: State) => {
	if (!target) return false;
	if ('tags' in target) {
		if (configHasEnabledVNC(target, state)) return true;
		if (configHasCustomVNCModule(target, state)) return true;
	} else {
		if (tagHasVNCStringModule(target, state)) return true;
		if (tagHasCustomVNCModule(target, state)) return true;
	}
	return false;
};

export const configVNCPassword = (config: Config, state: State, availableModules: Module[]) => {
	const vncModuleSettings =
		config.modules.find(isVNCModule) ||
		config.tags
			.flatMap((tag) => state.tags.find((t) => t.identifier === tag)?.modules)
			.find(isVNCModule);
	if (!vncModuleSettings) return 'password';
	const vncModule = availableModules.find(isVNCModule);
	const password =
		'vnc_password' in vncModuleSettings.settings
			? vncModuleSettings.settings.vnc_password
			: vncModule?.settings.vnc_password.default;
	return password;
};
