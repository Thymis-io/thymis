<script lang="ts">
	import { t } from 'svelte-i18n';
	import { DarkMode, NavBrand, NavHamburger, ToolbarButton } from 'flowbite-svelte';
	import BookOpen from 'lucide-svelte/icons/book-open';
	import Globe from 'lucide-svelte/icons/globe';
	import UserMenu from './UserMenu.svelte';
	import GlobalSearch from './GlobalSearch.svelte';
	import GithubIcon from './GithubIcon.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import type { Nav } from '../../routes/(authenticated)/+layout';

	interface Props {
		nav?: Nav;
		globalState?: GlobalState;
		authenticated?: boolean;
		drawerHidden: boolean;
		class?: string;
	}

	let {
		nav,
		globalState,
		authenticated = true,
		drawerHidden = $bindable(),
		class: clazz = ''
	}: Props = $props();
</script>

<div class="flex flex-nowrap justify-between mx-2 sm:mx-4 {clazz || ''}" color="default">
	<div class="flex items-center gap-2 sm:gap-4">
		{#if authenticated}
			<NavHamburger onClick={() => (drawerHidden = !drawerHidden)} class="m-0 md:block lg:hidden" />
		{/if}
		<NavBrand href="/" aria-label="Thymis Home">
			<img src="/favicon.png" class="w-6 min-w-6 sm:w-6 sm:min-w-6" alt="Thymis Logo" />
			<span class="ml-2 text-xl sm:text-2xl font-semibold dark:text-white hidden sm:block">
				Thymis
			</span>
		</NavBrand>
		{#if authenticated && globalState && nav}
			<div class="ms-2 w-2 sm:w-48 lg:w-64 xl:w-96 block">
				<GlobalSearch {globalState} {nav} />
			</div>
		{/if}
	</div>
	<div class="flex items-center sm:gap-2 p-1">
		<ToolbarButton
			size="lg"
			class="flex items-center gap-1 text-base"
			href="https://thymis.io/"
			ariaLabel="Thymis Website"
			title={$t('common.website')}
		>
			<Globe size="1.2em" />
			<span class="hidden lg:block">{$t('common.website')}</span>
		</ToolbarButton>
		<ToolbarButton
			size="lg"
			class="flex items-center gap-1 text-base"
			href="https://thymis.io/docs/"
			ariaLabel="Thymis Documentation"
			title={$t('common.documentation')}
		>
			<BookOpen size="18" />
			<span class="hidden lg:block">{$t('common.documentation')}</span>
		</ToolbarButton>
		<ToolbarButton
			size="lg"
			class="flex items-center gap-1 text-base"
			href="https://github.com/thymis-io/thymis"
			ariaLabel="Star Thymis on GitHub"
			title={$t('common.github')}
		>
			<GithubIcon />
			<span class="hidden lg:block">{$t('common.github')}</span>
		</ToolbarButton>
		<DarkMode />
		{#if authenticated}
			<UserMenu />
		{/if}
	</div>
</div>
