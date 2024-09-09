import type { Device, Module, ModuleSettings, State, Tag } from '$lib/state';

const isVNCModule = (module: ModuleSettings) => module.type.toLowerCase().includes('vnc');

const tagHasVNCStringModule = (tag: Tag, state: State) => tag.modules.some(isVNCModule);

const deviceHasVNCStringModule = (device: Device, state: State) =>
	device.modules.some(isVNCModule) ||
	device.tags.some((tag) => {
		const tagObj = state.tags.find((t) => t.identifier === tag);
		if (!tagObj) return false;
		return tagHasVNCStringModule(tagObj, state);
	});

const builtInKioskVNCModuleDetect = (target: Device | Tag, state: State) => {
	const kioskModuleType = 'thymis_controller.modules.kiosk.Kiosk';
	let module;
	if ('tags' in target) {
		const device = target;
		module =
			device.modules.find((module) => module.type === kioskModuleType) ||
			device.tags
				.flatMap((tag) => state.tags.find((t) => t.identifier === tag)?.modules)
				.find((module) => module?.type === kioskModuleType);
	} else {
		const tag = target;
		module = tag.modules.find((module) => module.type === kioskModuleType);
	}
	if (!module) return false;
	return 'enable_vnc' in module.settings ? module.settings.enable_vnc : false;
};

export const targetShouldShowVNC = (target: Device | Tag, state: State) => {
	if ('tags' in target) {
		if (deviceHasVNCStringModule(target, state)) return true;
		if (builtInKioskVNCModuleDetect(target, state)) return true;
	} else {
		if (tagHasVNCStringModule(target, state)) return true;
		if (builtInKioskVNCModuleDetect(target, state)) return true;
	}
	return false;
};

export const deviceVNCPassword = (device: Device, state: State, availableModules: Module[]) => {
	const kioskModuleType = 'thymis_controller.modules.kiosk.Kiosk';
	const kioskModuleSettings =
		device.modules.find((module) => module.type === kioskModuleType) ||
		device.tags
			.flatMap((tag) => state.tags.find((t) => t.identifier === tag)?.modules)
			.find((module) => module?.type === kioskModuleType);
	if (!kioskModuleSettings) return '';
	const kioskModule = availableModules.find((module) => module.type === kioskModuleType);
	// return "vnc_password" in kioskModule.settings ? kioskModule.settings.vnc_password : '';
	const password =
		'vnc_password' in kioskModuleSettings.settings
			? kioskModuleSettings.settings.vnc_password
			: kioskModule?.settings.vnc_password.default;
	return password;
};
