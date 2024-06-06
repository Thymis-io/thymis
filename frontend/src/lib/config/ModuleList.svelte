<script lang="ts">
	import type { Device, Module, Tag } from '$lib/state';
	import { P } from 'flowbite-svelte';
	import { page } from '$app/stores';
	import {
		deviceConfigUrl,
		selectedConfigTarget,
		selectedConfigContext,
		selectedConfigModule
	} from '$lib/deviceSelectHelper';

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
</script>

<div class="flex gap-2 mb-2 ml-1">
	<slot name="icon" />
	<P>{target?.displayName}</P>
</div>
<div class="mb-4">
	{#if target && context}
		{#each selfModules as module}
			<a
				href="/config?{deviceConfigUrl($page.url.search, module, context, target.identifier)}"
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
