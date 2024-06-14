<script lang="ts">
	import type { Device, Module, Tag } from '$lib/state';
	import { P, ToolbarButton } from 'flowbite-svelte';
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

	export let context: string | null;
	export let target: Tag | Device | undefined;
	export let selfModules: Module[];

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
			<a
				href="/config?{deviceConfigUrl(
					$page.url.search,
					module,
					$selectedContext,
					$selectedTarget?.identifier,
					context,
					target.identifier
				)}"
				class={`block p-2 rounded ${
					isSelected(module, $selectedConfigModule, $selectedConfigContext, $selectedConfigTarget)
						? 'bg-gray-200 dark:bg-gray-600'
						: 'hover:bg-gray-300 dark:hover:bg-gray-700'
				}`}
			>
				<P>{module.displayName}</P>
			</a>
		{/each}
	{/if}
</div>
