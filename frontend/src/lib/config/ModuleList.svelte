<script lang="ts">
	import { t } from 'svelte-i18n';
	import {
		globalNavSelectedTarget,
		saveState,
		type Device,
		type Module,
		type ModuleSettings,
		type Tag,
		globalNavSelectedTargetType
	} from '$lib/state';
	import { Modal, P, ToolbarButton, Tooltip } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import Pen from 'lucide-svelte/icons/pen';
	import Plus from 'lucide-svelte/icons/plus';
	import Trash from 'lucide-svelte/icons/trash';
	import { buildConfigSelectModuleSearchParam } from '$lib/searchParamHelpers';

	export let contextType: string | null;
	export let context: Tag | Device | undefined;

	export let selfModules: Module[];
	export let availableModules: Module[] = [];
	export let configSelectedModule: Module | undefined;
	export let configSelectedModuleContextType: string | null;
	export let configSelectedModuleContext: Tag | Device | undefined;

	const addModule = (target: Tag | Device | undefined, module: Module) => {
		if (target && !target.modules.find((m) => m.type === module.type)) {
			target.modules = [...target.modules, { type: module.type, settings: {} }];
			saveState();
		}
		addModuleModalOpen = false;
	};

	export let removeModule:
		| ((target: Tag | Device | undefined, module: Module) => void)
		| undefined = undefined;

	let addModuleModalOpen = false;

	$: isSelected = (
		module: Module,
		selectedConfigModule: Module | undefined,
		selectedConfigContext: string | null,
		selectedConfigTarget: Tag | Device | undefined
	) =>
		module.type === selectedConfigModule?.type &&
		contextType === selectedConfigContext &&
		context?.identifier === selectedConfigTarget?.identifier;

	$: console.log(context?.displayName, contextType);
</script>

<div class="flex justify-between mb-2">
	<div class="flex gap-2 inline-block items-center">
		<slot name="icon" />
		<P>{context?.displayName}</P>
	</div>
	{#if $globalNavSelectedTarget?.identifier !== context?.identifier}
		<ToolbarButton
			href="/config?{buildConfigSelectModuleSearchParam(
				$page.url.search,
				contextType,
				context?.identifier,
				contextType,
				context?.identifier,
				configSelectedModule
			)}"
		>
			<Pen />
		</ToolbarButton>
		<Tooltip type="auto">
			<P size="sm">{$t('config.edit_tag_modules')}</P>
		</Tooltip>
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
						configSelectedModuleContextType,
						configSelectedModuleContext
					)
						? 'bg-gray-300 dark:bg-gray-600'
						: 'hover:bg-gray-200 dark:hover:bg-gray-700'
				}`}
			>
				<a
					href="/config?{buildConfigSelectModuleSearchParam(
						$page.url.search,
						$globalNavSelectedTargetType,
						$globalNavSelectedTarget?.identifier,
						contextType,
						context.identifier,
						module
					)}"
					class={`block p-2 w-full flex gap-2`}
					data-sveltekit-noscroll
				>
					<img src={module.icon ?? '/favicon.png'} alt={module.displayName} class="w-6 h-6" />
					<P>{module.displayName}</P>
				</a>
				{#if removeModule && (!('targetHost' in context) || module.type !== 'thymis_controller.modules.thymis.ThymisDevice')}
					<button
						class="m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-500"
						on:click={() => removeModule(context, module)}
					>
						<Trash size={20} />
					</button>
					<Tooltip type="auto">
						<P size="sm">{$t('config.remove_module')}</P>
					</Tooltip>
				{/if}
			</div>
		{/each}
	{/if}
	{#if removeModule}
		<button
			class="p-2 w-full flex justify-center rounded hover:bg-gray-200 dark:hover:bg-gray-700"
			on:click={() => (addModuleModalOpen = true)}
		>
			<Plus />
		</button>
		<Tooltip type="auto">
			<P size="sm">{$t('config.add_module')}</P>
		</Tooltip>
		<Modal title={$t('config.add_module')} bind:open={addModuleModalOpen} autoclose outsideclose>
			<div class="grid gap-1">
				{#each availableModules as module}
					<button
						class="btn m-0 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2"
						on:click={() => addModule(context, module)}
					>
						<img src={module.icon ?? '/favicon.png'} alt={module.displayName} class="w-6 h-6" />
						<P>{module.displayName}</P>
					</button>
				{/each}
			</div>
		</Modal>
	{/if}
</div>
