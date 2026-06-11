<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState, type Config, type Module, type ModuleSettings, type Tag } from '$lib/state';
	import { Modal, Tooltip } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import Pen from 'lucide-svelte/icons/pen';
	import Plus from 'lucide-svelte/icons/plus';
	import Trash from 'lucide-svelte/icons/trash';
	import { buildConfigSelectModuleSearchParam } from '$lib/searchParamHelpers';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import { goto } from '$app/navigation';
	import ModuleIcon from './ModuleIcon.svelte';
	import type { Nav } from '../../routes/(authenticated)/+layout';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		contextType: string | null;
		context: Tag | Config | undefined;
		selfModules: Module[];
		availableModules?: Module[];
	}

	let {
		nav,
		globalState,
		contextType,
		context,
		selfModules,
		availableModules = []
	}: Props = $props();

	let moduleToRemove: Module | undefined = $state();

	const goToModule = async (module: Module | undefined) => {
		await goto(
			`/configuration/edit?${buildConfigSelectModuleSearchParam(
				globalState,
				$page.url.search,
				nav.selectedTargetType,
				nav.selectedTargetIdentifier,
				contextType,
				context?.identifier,
				module
			)}`
		);
	};

	const addModule = async (target: Tag | Config | undefined, module: Module) => {
		if (target && !target.modules.find((m) => m.type === module.type)) {
			target.modules = [...target.modules, { type: module.type, settings: {} }];
			globalState.save();
		}
		addModuleModalOpen = false;
		await goToModule(module);
	};

	const removeModule = (target: Tag | Config | undefined, module: ModuleSettings | Module) => {
		if (target) {
			target.modules = target.modules.filter((m) => m.type !== module.type);
		}
		saveState(globalState);
		goToModule(globalState.selectedModule);
	};

	let canChangeModules = $derived(
		contextType === nav.selectedTargetType && context?.identifier === nav.selectedTarget?.identifier
	);

	let addModuleModalOpen = $state(false);

	let isSelected = $derived(
		(
			module: Module,
			selectedConfigModule: Module | undefined,
			selectedConfigContext: string | null,
			selectedConfigTarget: Tag | Config | undefined
		) =>
			module.type === selectedConfigModule?.type &&
			contextType === selectedConfigContext &&
			context?.identifier === selectedConfigTarget?.identifier
	);
</script>

<DeleteConfirm
	target={moduleToRemove?.displayName}
	on:confirm={() => moduleToRemove && removeModule(context, moduleToRemove)}
	on:cancel={() => (moduleToRemove = undefined)}
/>
<div class="flex justify-between mb-2">
	<div class="font-semibold text-[var(--ds-text)] flex gap-2 items-center">
		<IdentifierLink
			identifier={context?.identifier}
			{globalState}
			context={contextType}
			iconSize="1.25rem"
		>
			{context?.displayName}
		</IdentifierLink>
	</div>
	{#if nav.selectedTarget?.identifier !== context?.identifier || nav.selectedTargetType !== contextType}
		<a
			class="ds-icon-btn"
			href="/configuration/edit?{buildConfigSelectModuleSearchParam(
				globalState,
				$page.url.search,
				contextType,
				context?.identifier,
				contextType,
				context?.identifier,
				nav.selectedModule
			)}"
		>
			<Pen size="18" />
		</a>
		<Tooltip type="auto">{$t('config.edit_tag_modules')}</Tooltip>
	{/if}
</div>
<div class="ml-2">
	{#if context && contextType}
		{#each selfModules as module}
			<div
				class={`flex items-center justify-between gap-1 rounded ${
					isSelected(
						module,
						nav.selectedModule,
						nav.selectedModuleContextType,
						nav.selectedModuleContext
					)
						? 'bg-[var(--ds-accent-dim)] text-[var(--ds-accent-strong)]'
						: 'hover:bg-[var(--ds-surface-2)]'
				}`}
			>
				<a
					href="/configuration/edit?{buildConfigSelectModuleSearchParam(
						globalState,
						$page.url.search,
						nav.selectedTargetType,
						nav.selectedTarget?.identifier,
						contextType,
						context.identifier,
						module
					)}"
					class={`block px-2 py-1.5 w-full flex gap-2 items-center`}
					data-sveltekit-noscroll
				>
					<ModuleIcon {module} />
					<span class="truncate text-sm">{module.displayName}</span>
				</a>
				{#if canChangeModules && (nav.selectedTargetType !== 'config' || module.type !== 'thymis_controller.modules.thymis.ThymisDevice')}
					<button class="ds-icon-btn self-center mr-1" onclick={() => (moduleToRemove = module)}>
						<Trash size={18} />
					</button>
					<Tooltip type="auto">{$t('config.remove_module')}</Tooltip>
				{/if}
			</div>
		{/each}
	{/if}
	{#if canChangeModules}
		<button
			id="add-module"
			class="mt-2 flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-[var(--ds-border-strong)] p-2 text-sm font-medium text-[var(--ds-text-dim)] transition-colors hover:border-[var(--ds-accent)] hover:bg-[var(--ds-accent-dim)] hover:text-[var(--ds-accent-strong)]"
			onclick={() => (addModuleModalOpen = true)}
		>
			<Plus size={16} />
			{$t('config.add_module')}
		</button>
		<Modal title={$t('config.add_module')} bind:open={addModuleModalOpen} autoclose outsideclose>
			<div class="grid gap-1">
				{#each availableModules as module}
					<button
						class="btn m-0 p-2 rounded-lg hover:bg-[var(--ds-surface-2)] flex items-center gap-2"
						onclick={() => addModule(context, module)}
					>
						<ModuleIcon {module} />
						<span class="text-sm">{module.displayName}</span>
					</button>
				{/each}
			</div>
		</Modal>
	{/if}
</div>
