import {
	HOST_PRIORITY,
	type Config,
	type Module,
	type ModuleSettingsWithOrigin,
	type SelectOneSettingType,
	type SettingType
} from '$lib/state';

/**
 * Priority a definition inherits from its tag/configuration, ignoring per-setting
 * overrides. Configurations use HOST_PRIORITY.
 */
export const inheritedSettingPriority = (
	definition: ModuleSettingsWithOrigin | undefined
): number | undefined => (definition ? (definition.priority ?? HOST_PRIORITY) : undefined);

/**
 * Priority a definition is emitted with for a given setting: the per-setting
 * override if present, else the priority inherited from its tag/configuration.
 *
 * NixOS module semantics: the lowest priority number wins.
 */
export const effectiveSettingPriority = (
	definition: ModuleSettingsWithOrigin | undefined,
	settingKey: string
): number | undefined =>
	definition?.priorities?.[settingKey] ?? inheritedSettingPriority(definition);

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

export const getAllowedImageFormatsForDeviceType = (
	deviceType: string,
	availableModules: Module[]
) => {
	const thymisDeviceModule = getThymisDeviceModule(availableModules);
	if (isASelectOneSetting(thymisDeviceModule?.settings['image_format'].type)) {
		return (thymisDeviceModule?.settings['image_format'].type['extra_data'] as any)
			?.restrict_values_on_other_key['device_type'][deviceType] as string[] | undefined;
	}
	return [];
};

export const getDeviceType = (config: Config | undefined) => {
	return config?.modules.find(
		(module) => module.type === 'thymis_controller.modules.thymis.ThymisDevice'
	)?.settings['device_type'] as string | undefined;
};

export const getConfigImageFormat = (config: Config | undefined) => {
	return config?.modules.find(
		(module) => module.type === 'thymis_controller.modules.thymis.ThymisDevice'
	)?.settings['image_format'] as string | undefined;
};
export const formatRamSize = (ramBytes: number | null | undefined) => {
	if (!ramBytes) return null;
	const gb = ramBytes / 1000 ** 3;
	if (gb >= 1) return `${Math.round(gb)}GB`;
	const mb = ramBytes / 1000 ** 2;
	return `${Math.round(mb)}MB`;
};
