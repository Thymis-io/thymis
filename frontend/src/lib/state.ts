import { invalidateButDeferUntilNavigation } from './notification';
import { fetchWithNotify } from './fetchWithNotify';

export type ModuleSettings = {
	type: string;
	settings: {
		[key: string]: unknown;
	};
};

export type Origin = {
	originId: string;
	originContext: string;
	originName: string;
};

export type ModuleSettingsWithOrigin = {
	type: string;
	settings: {
		[key: string]: unknown;
	};
	originId: string;
	originContext: string;
	originName: string;
	priority: number | undefined;
};

export type SecretType = 'single_line' | 'multi_line' | 'env_list' | 'file';
export type SecretProcessingType = 'none' | 'mkpasswd-yescrypt';

export type Secret = {
	id: string;
	display_name: string;
	type: SecretType;
	value_str: string | null;
	value_size: number;
	filename: string | null;
	include_in_image: boolean;
	processing_type: SecretProcessingType;
	error?: string | null;
	created_at: string;
	updated_at: string;
	delete_at: string | null;
};

export type SelectOneSettingType = {
	'select-one': [string, string][];
	'extra-data'?: Record<string, unknown>;
};

export type ListSettingType = {
	'list-of': Record<string, Setting>;
	'element-name'?: string;
};

export type SecretSettingType = {
	type: 'secret';
	'allowed-types'?: SecretType[];
	'default-processing-type'?: SecretProcessingType;
	'default-save-to-image'?: boolean;
};

export type ArtifactSettingType = {
	type: 'artifact';
};

export type TextAreaCodeSettingType = {
	type: 'textarea-code';
	language?: string;
};

export type SystemdTimerSetting = {
	timer_type?: 'realtime' | 'monotonic' | 'continuous';
	on_boot_sec?: string;
	on_unit_active_sec?: string;
	accuracy_sec?: string;
	on_calendar?: string[];
	persistent?: boolean;
	randomized_delay_sec?: string;
};

export type SystemdTimerSettingType = {
	type: 'systemd-timer';
} & SystemdTimerSetting;

export type SettingType =
	| 'string'
	| 'number'
	| 'bool'
	| 'textarea'
	| 'int'
	| SelectOneSettingType
	| ListSettingType
	| SecretSettingType
	| ArtifactSettingType
	| TextAreaCodeSettingType;

export type Setting<T extends SettingType = SettingType> = {
	displayName: string;
	type: T;
	description?: string | null;
	default?: unknown | null;
	example?: string | null;
	order?: number;
};

export type Module = {
	type: string;
	icon: string | undefined;
	iconDark: string | undefined;
	displayName: string;
	settings: Record<string, Setting>;
};

export type Tag = {
	displayName: string;
	identifier: string;
	priority: number;
	modules: ModuleSettings[];
};

export type Config = {
	displayName: string;
	identifier: string;
	modules: ModuleSettings[];
	tags: string[];
};

export type Repo = {
	url: string;
	api_key_secret: string | null;
};

export type State = {
	version: string;
	repositories: { [name: string]: Repo };
	configs: Config[];
	tags: Tag[];
};

export const saveState = async (state: State) => {
	const response = await fetchWithNotify(`/api/state`, {
		method: 'PATCH',
		headers: {
			'content-type': 'application/json'
		},
		body: JSON.stringify({
			version: state.version,
			repositories: state.repositories,
			configs: state.configs,
			tags: state.tags
		})
	});
	await invalidateButDeferUntilNavigation((url) => url.pathname === '/api/state');
	return response.ok;
};

export const build = async () => {
	await fetchWithNotify(`/api/action/build`, { method: 'POST' });
};

export const getTagByIdentifier = (state: State, identifier: string | null) => {
	if (!identifier) return undefined;
	return state.tags.find((tag) => tag.identifier === identifier);
};

export const getConfigByIdentifier = (state: State, identifier: string | null) => {
	if (!identifier) return undefined;
	return state.configs.find((config) => config.identifier === identifier);
};

export type ContextType = 'tag' | 'config';
