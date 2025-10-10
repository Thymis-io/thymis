<script lang="ts">
	import type { Module } from '$lib/state';

	interface Props {
		module: Module;
		theme?: 'auto' | 'dark' | 'light';
		imageClass?: string;
	}

	let { module, theme = 'auto', imageClass = 'w-5' } = $props();

	let iconLight = $derived(module.icon ?? module.iconDark ?? '/ModuleIcon.svg');
	let iconDark = $derived(module.iconDark ?? module.icon ?? '/ModuleIcon_dark.svg');
</script>

{#if theme === 'auto'}
	<img src={iconLight} alt={module.displayName} class={`block dark:hidden ${imageClass}`} />
	<img src={iconDark} alt={module.displayName} class={`hidden dark:block ${imageClass}`} />
{:else if theme === 'light'}
	<img src={iconLight} alt={module.displayName} class={`${imageClass}`} />
{:else if theme === 'dark'}
	<img src={iconDark} alt={module.displayName} class={`${imageClass}`} />
{/if}
