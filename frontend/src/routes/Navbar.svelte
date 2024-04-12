<script lang="ts">
	import UserMenu from '$lib/UserMenu.svelte';
	import { DarkMode, NavBrand, NavHamburger, Navbar, Search, ToolbarButton } from 'flowbite-svelte';
	import { BellSolid, GithubSolid } from 'flowbite-svelte-icons';
	import '../app.postcss';

	export let fluid = true;

	export let drawerHidden: boolean;
</script>

<Navbar {fluid} color="default">
	<div class="flex w-fit items-center justify-start">
		<NavHamburger
			onClick={() => (drawerHidden = !drawerHidden)}
			class="m-0 me-3 md:block lg:hidden"
		/>
		<NavBrand href="/" class="ms-2 md:me-24">
			<img src="/favicon.png" class="me-3 h-6 sm:h-8" alt="Thymis Logo" />
			<span class="self-center whitespace-nowrap text-xl font-semibold dark:text-white sm:text-2xl">
				Thymis
			</span>
		</NavBrand>
		<div class="w-96">
			<Search size="md" />
		</div>
	</div>

	<div class="ms-auto flex items-center gap-2 p-1">
		<a
			class="github-button"
			href="https://github.com/thymis-io/thymis"
			aria-label="Star thymis-io/thymis on GitHub"
		>
			<ToolbarButton size="lg">
				<GithubSolid />
			</ToolbarButton>
		</a>
		<UserMenu />
		<DarkMode />
	</div>
</Navbar>
