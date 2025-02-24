<script lang="ts">
	import type { Module } from '$lib/state';

	export let module: Module;
</script>

<img
	src={module.icon ?? module.iconDark ?? '/ModuleIcon.svg'}
	alt={module.displayName}
	class="w-5 block dark:hidden"
/>
<img
	src={module.iconDark ?? module.icon ?? '/ModuleIcon_dark.svg'}
	alt={module.displayName}
	class="w-5 hidden dark:block"
/>
