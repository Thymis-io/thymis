<script lang="ts">
	import type { Module } from '$lib/state';

	export let module: Module;
	export let theme: 'auto' | 'dark' | 'light' = 'auto';

	let iconLight = module.icon ?? module.iconDark ?? '/ModuleIcon.svg';
	let iconDark = module.iconDark ?? module.icon ?? '/ModuleIcon_dark.svg';
</script>

{#if theme === 'auto'}
	<img src={iconLight} alt={module.displayName} class="w-5 block dark:hidden" />
	<img src={iconDark} alt={module.displayName} class="w-5 hidden dark:block" />
{:else if theme === 'light'}
	<img src={iconLight} alt={module.displayName} class="w-5" />
{:else if theme === 'dark'}
	<img src={iconDark} alt={module.displayName} class="w-5" />
{/if}
