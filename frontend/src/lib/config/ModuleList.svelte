<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Device, Module, Tag } from '$lib/state';
	import { Modal, P, ToolbarButton } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import {
		deviceUrl,
		deviceConfigUrl,
		selectedTarget,
		selectedConfigTarget,
		selectedConfigContext,
		selectedConfigModule,
		selectedContext
	} from '$lib/deviceSelectHelper';
	import Pen from 'lucide-svelte/icons/pen';
	import Plus from 'lucide-svelte/icons/plus';
	import Minus from 'lucide-svelte/icons/minus';

	export let context: string | null;
	export let target: Tag | Device | undefined;
	export let selfModules: Module[];
	export let canChangeModules: boolean = false;
	export let availableModules: Module[] = [];
	export let addModule: (target: Tag | Device | undefined, module: Module) => void = () => {};
	export let removeModule: (target: Tag | Device | undefined, module: Module) => void = () => {};

	let addModuleModalOpen = false;

	$: isSelected = (
		module: Module,
		selectedConfigModule: Module | undefined,
		selectedConfigContext: string | null,
		selectedConfigTarget: Tag | Device | undefined
	) =>
		module.type === selectedConfigModule?.type &&
		context === selectedConfigContext &&
		target?.identifier === selectedConfigTarget?.identifier;

	$: console.log(target?.displayName, context);
</script>

<div class="flex justify-between mb-2 ml-1">
	<div class="flex gap-2 inline-block items-center">
		<slot name="icon" />
		<P>{target?.displayName}</P>
	</div>
	{#if $selectedTarget?.identifier !== target?.identifier}
		<ToolbarButton
			href="/config?{deviceConfigUrl(
				$page.url.search,
				$selectedConfigModule,
				context,
				target?.identifier,
				context,
				target?.identifier
			)}"
		>
			<Pen />
		</ToolbarButton>
	{/if}
</div>
<div class="mb-6">
	{#if target && context}
		{#each selfModules as module}
			<div
				class={`flex justify-between gap-1 rounded ${
					isSelected(module, $selectedConfigModule, $selectedConfigContext, $selectedConfigTarget)
						? 'bg-gray-300 dark:bg-gray-600'
						: 'hover:bg-gray-200 dark:hover:bg-gray-700'
				}`}
			>
				<a
					href="/config?{deviceConfigUrl(
						$page.url.search,
						module,
						$selectedContext,
						$selectedTarget?.identifier,
						context,
						target.identifier
					)}"
					class={`block p-2 w-full`}
				>
					<P>{module.displayName}</P>
				</a>
				{#if canChangeModules}
					<button
						class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-500"
						on:click={() => removeModule(target, module)}
					>
						<Minus />
					</button>
				{/if}
			</div>
		{/each}
	{/if}
	{#if canChangeModules}
		<div>
			<button
				class="btn m-1 p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600"
				on:click={() => (addModuleModalOpen = true)}
			>
				<Plus />
			</button>
		</div>
		<Modal title={$t('config.add_module')} bind:open={addModuleModalOpen} autoclose outsideclose>
			<div class="grid gap-1">
				{#each availableModules as module}
					<button
						class="btn m-0 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center gap-2"
						on:click={() => addModule(target, module)}
					>
						<img src={module.icon ?? '/favicon.png'} alt={module.displayName} class="w-6 h-6" />
						<P>{module.displayName}</P>
					</button>
				{/each}
			</div>
		</Modal>
	{/if}
</div>
