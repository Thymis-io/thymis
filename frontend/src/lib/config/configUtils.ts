import type { Device, Module, SelectOneSettingType, SettingType } from '$lib/state';

export const isASelectOneSetting = (
	type: SettingType | undefined
): type is SelectOneSettingType => {
	return (
		!!type && typeof type === 'object' && 'select-one' in type && Array.isArray(type['select-one'])
	);
};

export const getModule = (modules: Module[], moduleType: string) => {
	return modules.find((module) => module.type === moduleType);
};

export const getThymisDeviceModule = (availableModules: Module[]) => {
	return getModule(availableModules, 'thymis_controller.modules.thymis.ThymisDevice');
};

export const getDeviceTypesMap = (availableModules: Module[]) => {
	const thymisDeviceModule = getThymisDeviceModule(availableModules);
	if (isASelectOneSetting(thymisDeviceModule?.settings['device_type'].type)) {
		return Object.fromEntries(
			thymisDeviceModule?.settings['device_type'].type['select-one'].map(([value, key]) => [
				key as string,
				value as string
			])
		);
	}
	return {};
};

export const getDeviceType = (device: Device | undefined) => {
	return device?.modules.find(
		(module) => module.type === 'thymis_controller.modules.thymis.ThymisDevice'
	)?.settings['device_type'] as string | undefined;
};

export const getConfigImageFormat = (device: Device | undefined) => {
	return device?.modules.find(
		(module) => module.type === 'thymis_controller.modules.thymis.ThymisDevice'
	)?.settings['image_format'] as string | undefined;
};
