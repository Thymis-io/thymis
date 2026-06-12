<script lang="ts">
	import { t } from 'svelte-i18n';
	import { saveState, type Config, type Module, type ModuleSettings, type Tag } from '$lib/state';
	import { Modal, Tooltip } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import Pen from 'lucide-svelte/icons/pen';
	import Plus from 'lucide-svelte/icons/plus';
	import Trash from 'lucide-svelte/icons/trash';
	import Search from 'lucide-svelte/icons/search';
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
	let moduleSearch = $state('');

	// modules that can still be added to this target (already-present ones, incl. the
	// mandatory Device module, are excluded)
	let addableModules = $derived(
		availableModules.filter((m) => !context?.modules?.find((cm) => cm.type === m.type))
	);

	let filteredModules = $derived(
		addableModules.filter((m) => {
			const q = moduleSearch.trim().toLowerCase();
			if (!q) return true;
			return (
				m.displayName.toLowerCase().includes(q) || (m.description ?? '').toLowerCase().includes(q)
			);
		})
	);

	// group by category, preserving the order categories first appear in availableModules
	let groupedModules = $derived.by(() => {
		const groups = new Map<string, Module[]>();
		for (const m of filteredModules) {
			const cat = m.category || $t('config.module_category_other');
			if (!groups.has(cat)) groups.set(cat, []);
			groups.get(cat)!.push(m);
		}
		return [...groups.entries()];
	});

	$effect(() => {
		if (!addModuleModalOpen) moduleSearch = '';
	});

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
		<Modal title={$t('config.add_module')} bind:open={addModuleModalOpen} outsideclose>
			<div class="flex flex-col gap-3">
				<div class="relative">
					<Search
						size={16}
						class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ds-text-mute)]"
					/>
					<!-- svelte-ignore a11y_autofocus -->
					<input
						type="text"
						bind:value={moduleSearch}
						placeholder={$t('config.search_modules')}
						autofocus
						class="w-full rounded-lg border border-[var(--ds-border)] bg-[var(--ds-surface)] py-2 pl-9 pr-3 text-sm text-[var(--ds-text)] placeholder:text-[var(--ds-text-mute)] focus:border-[var(--ds-accent)] focus:outline-none"
					/>
				</div>

				{#if groupedModules.length === 0}
					<p class="py-6 text-center text-sm text-[var(--ds-text-mute)]">
						{$t('config.no_modules_found')}
					</p>
				{/if}

				{#each groupedModules as [category, mods] (category)}
					<div class="flex flex-col gap-0.5">
						<div
							class="px-1 pb-1 text-[10.5px] font-semibold uppercase tracking-wider text-[var(--ds-text-mute)]"
						>
							{category}
						</div>
						{#each mods as module (module.type)}
							<button
								class="flex w-full items-center gap-3 rounded-lg p-2 text-left hover:bg-[var(--ds-surface-2)]"
								onclick={() => addModule(context, module)}
							>
								<ModuleIcon {module} />
								<span class="flex min-w-0 flex-col">
									<span class="truncate text-sm font-medium text-[var(--ds-text)]"
										>{module.displayName}</span
									>
									{#if module.description}
										<span class="truncate text-xs text-[var(--ds-text-mute)]"
											>{module.description}</span
										>
									{/if}
								</span>
							</button>
						{/each}
					</div>
				{/each}
			</div>
		</Modal>
	{/if}
</div>
