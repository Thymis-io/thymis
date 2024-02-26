<script lang="ts">
	import AppsMenu from '$lib/AppsMenu.svelte';
	import { DarkMode, NavBrand, NavHamburger, Navbar, Search, ToolbarButton } from 'flowbite-svelte';
	import { BellSolid } from 'flowbite-svelte-icons';
	import '../app.postcss';

	export let fluid = true;
</script>

<Navbar {fluid} color="default">
	<div class="flex w-fit items-center justify-start">
		<NavHamburger />
		<NavBrand href="/" class="ms-2 md:me-24">
			<img src="/favicon.png" class="me-3 h-6 sm:h-8" alt="Flowbite Logo" />
			<span class="self-center whitespace-nowrap text-xl font-semibold dark:text-white sm:text-2xl">
				Flowbite
			</span>
		</NavBrand>
		<div class="w-96">
			<Search size="md" />
		</div>
	</div>

	<div class="ms-auto flex items-center gap-2 p-1">
		<a
			class="github-button"
			href="https://github.com/themesberg/flowbite-svelte-admin-dashboard"
			data-color-scheme="no-preference: dark; light: light; dark: light;"
			data-icon="octicon-star"
			data-size="large"
			data-show-count="true"
			aria-label="Star themesberg/flowbite-svelte-admin-dashboard on GitHub">Star</a
		>
		<ToolbarButton size="lg"><BellSolid /></ToolbarButton>
		<AppsMenu />
		<DarkMode />
	</div>
</Navbar>
