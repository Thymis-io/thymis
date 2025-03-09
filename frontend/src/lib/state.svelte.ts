import {
	saveState,
	type Config,
	type ContextType,
	type Module,
	type Repo,
	type State,
	type Tag
} from './state';

export class GlobalState {
	repositories = $state<{ [name: string]: Repo }>()!;
	configs = $state<Config[]>()!;
	tags = $state<Tag[]>()!;
	availableModules = $state<Module[]>()!;

	selectedTargetType = $state<ContextType | null>(null);
	selectedTargetIdentifier = $state<string | null>(null);
	selectedConfig = $derived.by(() =>
		this.selectedTargetType === 'config' ? this.config(this.selectedTargetIdentifier) : undefined
	);
	selectedTag = $derived.by(() =>
		this.selectedTargetType === 'tag' ? this.tag(this.selectedTargetIdentifier) : undefined
	);
	selectedTarget = $derived.by(() => this.selectedConfig || this.selectedTag);

	selectedModuleContextType = $state<ContextType | null>(null);
	selectedModuleContextIdentifier = $state<string | null>(null);
	selectedModuleType = $state<string | null>(null);
	selectedModuleContextConfig = $derived.by(() =>
		this.selectedModuleContextType === 'config'
			? this.config(this.selectedModuleContextIdentifier)
			: undefined
	);
	selectedModuleContextTag = $derived.by(() =>
		this.selectedModuleContextType === 'tag'
			? this.tag(this.selectedModuleContextIdentifier)
			: undefined
	);
	selectedModuleContext = $derived.by(
		() => this.selectedModuleContextConfig || this.selectedModuleContextTag
	);
	selectedModule = $derived.by(() =>
		this.availableModules.find((module) => module.type === this.selectedModuleType)
	);

	selectedModuleSettings = $derived.by(() =>
		this.selectedModuleContext?.modules?.find((s) => s.type === this.selectedModule?.type)
	);

	constructor(state: State, urlParams: URLSearchParams, availableModules: Module[]) {
		this.repositories = state.repositories;
		this.configs = state.configs;
		this.tags = state.tags;
		this.availableModules = availableModules;

		this.selectedTargetType = urlParams.get('global-nav-target-type') as ContextType;
		this.selectedTargetIdentifier = urlParams.get('global-nav-target');

		this.selectedModuleContextType = urlParams.get(
			'config-selected-module-context-type'
		) as ContextType;
		this.selectedModuleContextIdentifier = urlParams.get(
			'config-selected-module-context-identifier'
		);
		this.selectedModuleType = urlParams.get('config-selected-module');
	}

	config = (identifier: string | null) => {
		if (!identifier) return undefined;
		return this.configs.find((config) => config.identifier === identifier);
	};

	tag = (identifier: string | null) => {
		if (!identifier) return undefined;
		return this.tags.find((tag) => tag.identifier === identifier);
	};

	save = () => {
		saveState({
			repositories: this.repositories,
			configs: this.configs,
			tags: this.tags
		});
	};
}
