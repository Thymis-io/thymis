import { invalidate } from '$app/navigation';
import { derived, writable } from 'svelte/store';
import { queryParam } from 'sveltekit-search-params';
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

// type ValueTypes = Literal["bool", "string", "path", "package", "textarea", "int"]

// class SelectOneType(BaseModel):
//     type: Literal["select-one"] = "select-one"
//     select_one: List[Tuple[str, str]] = Field(serialization_alias="select-one")
//     extra_data: Optional[dict[str, JsonValue]] = Field(default=None)

// class ListType(BaseModel):
//     type: Literal["list"] = "list"
//     settings: dict[str, "Setting"] = Field(serialization_alias="list-of")
//     element_name: Optional[str] = Field(
//         serialization_alias="element-name", default=None
//     )

// class SecretType(BaseModel):
//     type: Literal["secret"] = "secret"
//     allowed_types: List[db_models.SecretTypes] = Field(
//         serialization_alias="allowed-types", default_factory=list
//     )
//     default_processing_type: db_models.SecretProcessingTypes = Field(
//         serialization_alias="default-processing-type",
//         default=db_models.SecretProcessingTypes.NONE,
//     )
//     default_save_to_image: bool = Field(
//         serialization_alias="default-save-to-image", default=False
//     )

// class InlineFileType(BaseModel):
//     type: Literal["inline-file"] = "inline-file"
//     accept: Optional[str] = None

// type SettingTypes = Union[ValueTypes, SelectOneType, ListType, SecretType, InlineFileType]

export type SecretType = 'single_line' | 'multi_line' | 'env_list' | 'file';
export type SecretProcessingType = 'none' | 'mkpasswd-yescrypt';

// A setting can be different types
export type Setting<T = any> = {
	displayName: string;
	description?: string;
	type: T;
	order?: number;
	default?: any;
	example?: string;
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

export type SettingType =
	| 'string'
	| 'number'
	| 'bool'
	| 'textarea'
	| 'int'
	| SelectOneSettingType
	| ListSettingType
	| SecretSettingType;

export type Setting<T extends SettingType = SettingType> = {
	displayName: string;
	type: T;
	default: string;
	description: string;
	example: string | null;
	order: number;
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
};

export type State = {
	repositories: { [name: string]: Repo };
	configs: Config[];
	tags: Tag[];
};

export const state = writable<State>();

export let currentState: State;

state.subscribe((value) => {
	currentState = value;
});

export const saveState = async () => {
	state.set(currentState);
	const response = await fetchWithNotify(`/api/state`, {
		method: 'PATCH',
		headers: {
			'content-type': 'application/json'
		},
		body: JSON.stringify(currentState)
	});
	await invalidate((url) => url.pathname === '/api/state');
	return response.ok;
};

export const build = async () => {
	await fetchWithNotify(`/api/action/build`, { method: 'POST' });
};

export const getTagByIdentifier = (state: State, identifier: string) => {
	return state.tags.find((tag) => tag.identifier === identifier);
};

export const getConfigByIdentifier = (state: State, identifier: string) => {
	return state.configs.find((config) => config.identifier === identifier);
};

export const globalNavSelectedTag = derived(
	[state, queryParam('global-nav-target-type'), queryParam('global-nav-target')],
	([$state, $context, $identifier]) => {
		if ($context === 'tag') {
			return getTagByIdentifier($state, $identifier);
		}
	}
);

export const globalNavSelectedConfig = derived(
	[state, queryParam('global-nav-target-type'), queryParam('global-nav-target')],
	([$state, $context, $identifier]) => {
		if ($context === 'config') {
			return getConfigByIdentifier($state, $identifier);
		}
	}
);

export const globalNavSelectedTarget = derived(
	[globalNavSelectedConfig, globalNavSelectedTag],
	([$globalNavSelectedConfig, $globalNavSelectedTag]) =>
		$globalNavSelectedConfig || $globalNavSelectedTag
);

export const globalNavSelectedTargetType = queryParam<ContextType>('global-nav-target-type');

export type ContextType = 'tag' | 'config';
