<script lang="ts">
	import { t } from 'svelte-i18n';
	import { DarkMode, NavBrand, NavHamburger, Search, ToolbarButton } from 'flowbite-svelte';
	import GithubSolid from 'flowbite-svelte-icons/GithubSolid.svelte';
	import LanguageSelect from './LanguageSelect.svelte';
	import UserMenu from './UserMenu.svelte';

	export let drawerHidden: boolean;
	let clazz = '';
	export { clazz as class };
</script>

<div class="flex flex-nowrap justify-between mx-2 sm:mx-4 {clazz || ''}" color="default">
	<div class="flex items-center gap-2 sm:gap-4">
		<NavHamburger onClick={() => (drawerHidden = !drawerHidden)} class="m-0 md:block lg:hidden" />
		<NavBrand href="/">
			<img src="/favicon.png" class="w-6 min-w-6 sm:w-8 sm:min-w-8" alt="Thymis Logo" />
			<span class="ml-2 text-xl sm:text-2xl font-semibold dark:text-white hidden sm:block">
				Thymis
			</span>
		</NavBrand>
		<div class="ms-2 w-2 sm:w-48 lg:w-64 xl:w-96 block">
			<Search size="md" placeholder={$t('common.search')} class="py-1 sm:py-2" />
		</div>
	</div>
	<div class="flex items-center sm:gap-2 p-1">
		<a
			class="github-button"
			href="https://github.com/thymis-io/thymis"
			aria-label="Star thymis-io/thymis on GitHub"
		>
			<ToolbarButton size="lg">
				<GithubSolid />
			</ToolbarButton>
		</a>
		<DarkMode />
		<UserMenu />
	</div>
</div>
