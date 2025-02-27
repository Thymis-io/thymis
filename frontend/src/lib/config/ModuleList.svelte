<script lang="ts">
	import { t } from 'svelte-i18n';
	import {
		globalNavSelectedTarget,
		saveState,
		type Config,
		type Module,
		type ModuleSettings,
		type Tag,
		globalNavSelectedTargetType,
		type ContextType
	} from '$lib/state';
	import { Modal, P, ToolbarButton, Tooltip } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import Pen from 'lucide-svelte/icons/pen';
	import Plus from 'lucide-svelte/icons/plus';
	import Trash from 'lucide-svelte/icons/trash';
	import {
		buildConfigSelectModuleSearchParam,
		configSelectedModuleContext,
		configSelectedModuleContextType
	} from '$lib/searchParamHelpers';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import { goto } from '$app/navigation';
	import ModuleIcon from './ModuleIcon.svelte';

	export let contextType: string | null;
	export let context: Tag | Config | undefined;

	export let selfModules: Module[];
	export let availableModules: Module[] = [];
	export let configSelectedModule: Module | undefined;

	let moduleToRemove: Module | undefined;

	const goToModule = async (module: Module | undefined) => {
		await goto(
			`/configuration/edit?${buildConfigSelectModuleSearchParam(
				$page.url.search,
				$globalNavSelectedTargetType,
				$globalNavSelectedTarget?.identifier,
				contextType,
				context?.identifier,
				module
			)}`
		);
	};

	const addModule = async (target: Tag | Config | undefined, module: Module) => {
		if (target && !target.modules.find((m) => m.type === module.type)) {
			target.modules = [...target.modules, { type: module.type, settings: {} }];
			await saveState();
		}
		addModuleModalOpen = false;
		await goToModule(module);
	};

	const removeModule = (target: Tag | Config | undefined, module: ModuleSettings | Module) => {
		if (target) {
			target.modules = target.modules.filter((m) => m.type !== module.type);
		}
		saveState();
		goToModule(undefined);
	};

	$: canChangeModules =
		contextType === $globalNavSelectedTargetType &&
		context?.identifier === $globalNavSelectedTarget?.identifier;

	let addModuleModalOpen = false;

	$: isSelected = (
		module: Module,
		selectedConfigModule: Module | undefined,
		selectedConfigContext: string | null,
		selectedConfigTarget: Tag | Config | undefined
	) =>
		module.type === selectedConfigModule?.type &&
		contextType === selectedConfigContext &&
		context?.identifier === selectedConfigTarget?.identifier;
</script>

<DeleteConfirm
	target={moduleToRemove?.displayName}
	on:confirm={() => moduleToRemove && removeModule(context, moduleToRemove)}
	on:cancel={() => (moduleToRemove = undefined)}
/>
<div class="flex justify-between mb-2">
	<div class="text-gray-900 dark:text-white font-semibold flex gap-2 items-center">
		<slot name="icon" />
		<span>{context?.displayName}</span>
	</div>
	{#if $globalNavSelectedTarget?.identifier !== context?.identifier || $globalNavSelectedTargetType !== contextType}
		<a
			class="m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 disabled:cursor-not-allowed disabled:opacity-50"
			href="/configuration/edit?{buildConfigSelectModuleSearchParam(
				$page.url.search,
				contextType,
				context?.identifier,
				contextType,
				context?.identifier,
				configSelectedModule
			)}"
		>
			<Pen size="20" />
		</a>
		<Tooltip type="auto">{$t('config.edit_tag_modules')}</Tooltip>
	{/if}
</div>
<div class="ml-2">
	{#if context && contextType}
		{#each selfModules as module}
			<div
				class={`flex justify-between gap-1 rounded ${
					isSelected(
						module,
						configSelectedModule,
						$configSelectedModuleContextType,
						$configSelectedModuleContext
					)
						? 'bg-gray-300 dark:bg-gray-600'
						: 'hover:bg-gray-200 dark:hover:bg-gray-700'
				}`}
			>
				<a
					href="/configuration/edit?{buildConfigSelectModuleSearchParam(
						$page.url.search,
						$globalNavSelectedTargetType,
						$globalNavSelectedTarget?.identifier,
						contextType,
						context.identifier,
						module
					)}"
					class={`block px-2 py-1.5 w-full flex gap-2 items-center`}
					data-sveltekit-noscroll
				>
					<ModuleIcon {module} />
					<P>{module.displayName}</P>
				</a>
				{#if canChangeModules && ($globalNavSelectedTargetType !== 'config' || module.type !== 'thymis_controller.modules.thymis.ThymisDevice')}
					<button
						class="m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-500"
						on:click={() => (moduleToRemove = module)}
					>
						<Trash size={20} />
					</button>
					<Tooltip type="auto">{$t('config.remove_module')}</Tooltip>
				{/if}
			</div>
		{/each}
	{/if}
	{#if canChangeModules}
		<button
			id="add-module"
			class="p-2 w-full flex justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700"
			on:click={() => (addModuleModalOpen = true)}
		>
			<Plus />
		</button>
		<Tooltip type="auto" triggeredBy="#add-module">{$t('config.add_module')}</Tooltip>
		<Modal title={$t('config.add_module')} bind:open={addModuleModalOpen} autoclose outsideclose>
			<div class="grid gap-1">
				{#each availableModules as module}
					<button
						class="btn m-0 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2"
						on:click={() => addModule(context, module)}
					>
						<ModuleIcon {module} />
						<P>{module.displayName}</P>
					</button>
				{/each}
			</div>
		</Modal>
	{/if}
</div>
