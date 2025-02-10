import type { Config, Module, ModuleSettings, State, Tag } from '$lib/state';

const isVNCModule = (module: ModuleSettings) => module.type.toLowerCase().includes('vnc');

const tagHasVNCStringModule = (tag: Tag, state: State) => tag.modules.some(isVNCModule);

const configHasVNCStringModule = (config: Config, state: State) =>
	config.modules.some(isVNCModule) ||
	config.tags.some((tag) => {
		const tagObj = state.tags.find((t) => t.identifier === tag);
		if (!tagObj) return false;
		return tagHasVNCStringModule(tagObj, state);
	});

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

const builtInKioskVNCModuleDetect = (target: Config | Tag, state: State) => {
	const kioskModuleType = 'thymis_controller.modules.kiosk.Kiosk';
	let module;
	if ('tags' in target) {
		const config = target;
		module =
			config.modules.find((module) => module.type === kioskModuleType) ||
			config.tags
				.flatMap((tag) => state.tags.find((t) => t.identifier === tag)?.modules)
				.find((module) => module?.type === kioskModuleType);
	} else {
		const tag = target;
		module = tag.modules.find((module) => module.type === kioskModuleType);
	}
	if (!module) return false;
	return 'enable_vnc' in module.settings ? module.settings.enable_vnc : false;
};

export const targetShouldShowVNC = (target: Config | Tag, state: State) => {
	if ('tags' in target) {
		if (configHasVNCStringModule(target, state)) return true;
		if (builtInKioskVNCModuleDetect(target, state)) return true;
		if (configHasCustomVNCModule(target, state)) return true;
	} else {
		if (tagHasVNCStringModule(target, state)) return true;
		if (builtInKioskVNCModuleDetect(target, state)) return true;
		if (tagHasCustomVNCModule(target, state)) return true;
	}
	return false;
};

export const configVNCPassword = (config: Config, state: State, availableModules: Module[]) => {
	const kioskModuleType = 'thymis_controller.modules.kiosk.Kiosk';
	const kioskModuleSettings =
		config.modules.find((module) => module.type === kioskModuleType) ||
		config.tags
			.flatMap((tag) => state.tags.find((t) => t.identifier === tag)?.modules)
			.find((module) => module?.type === kioskModuleType);
	if (!kioskModuleSettings) return 'password';
	const kioskModule = availableModules.find((module) => module.type === kioskModuleType);
	// return "vnc_password" in kioskModule.settings ? kioskModule.settings.vnc_password : '';
	const password =
		'vnc_password' in kioskModuleSettings.settings
			? kioskModuleSettings.settings.vnc_password
			: kioskModule?.settings.vnc_password.default;
	return password;
};
