<script lang="ts">
	import { t } from 'svelte-i18n';
	import UserMenu from './UserMenu.svelte';
	import { DarkMode, NavBrand, NavHamburger, Navbar, Search, ToolbarButton } from 'flowbite-svelte';
	import GithubSolid from 'flowbite-svelte-icons/GithubSolid.svelte';
	import LanguageSelect from './LanguageSelect.svelte';

	export let fluid = true;

	export let drawerHidden: boolean;
	let clazz = '';
	export { clazz as class };
</script>

<Navbar {fluid} class={clazz || ''} color="default">
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
		<div class="w-8 lg:hidden">
			<Search size="md" placeholder={$t('common.search')} />
		</div>
		<div class="w-96 hidden lg:block">
			<Search size="md" placeholder={$t('common.search')} />
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
		<LanguageSelect />
	</div>
</Navbar>
