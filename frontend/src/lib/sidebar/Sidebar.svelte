<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { t, locale } from 'svelte-i18n';
	import { Sidebar, SidebarGroup, SidebarWrapper } from 'flowbite-svelte';
	import Settings from 'lucide-svelte/icons/settings';
	import ChartBar from 'lucide-svelte/icons/chart-bar';
	import Server from 'lucide-svelte/icons/server';
	import GitBranch from 'lucide-svelte/icons/git-graph';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import FileLock from 'lucide-svelte/icons/file-lock-2';
	import FolderOpen from 'lucide-svelte/icons/folder-open';
	import type { GlobalState } from '$lib/state.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

	interface Props {
		globalState: GlobalState;
		drawerHidden: boolean;
		asideClass?: string;
	}

	let { globalState, drawerHidden = $bindable(), asideClass = '' }: Props = $props();

	const closeDrawer = () => {
		drawerHidden = true;
	};

	let spanClass = 'ms-4';
	let childClass =
		'p-1 hover:bg-gray-100 text-gray-500 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200 ';

	let nonActiveClass =
		childClass + ' hover:cursor-pointer dark:text-gray-400 hover:text-black dark:hover:text-white';
	let activeClass = childClass + ' cursor-default text-primary-600 dark:text-primary-400';

	let mainSidebarUrl = $derived($page.url.pathname);
	let activeMainSidebar: string = $state('');

	afterNavigate((navigation) => {
		// this fixes https://github.com/themesberg/flowbite-svelte/issues/364
		document.getElementById('svelte')?.scrollTo({ top: 0 });
		closeDrawer();

		activeMainSidebar = navigation.to?.url.pathname ?? '';
	});

	type NavItem = {
		name: string;
		icon: any;
		href: string;
		hidden?: boolean;
		children?: Record<string, string>;
	};

	let anyTargetHasVNC = $derived(
		globalState.configs.some((config) => targetShouldShowVNC(config, globalState)) ||
			globalState.tags.some((tag) => targetShouldShowVNC(tag, globalState))
	);

	let navItems: NavItem[] = $derived([
		{
			name: $t('nav.overview'),
			icon: ChartBar,
			href: '/overview'
		},
		{
			name: $t('nav.configurations'),
			icon: FileCode,
			href: '/configuration/list'
		},
		{
			name: $t('nav.tags'),
			icon: TagIcon,
			href: '/tags'
		},
		{
			name: $t('nav.devices'),
			icon: Server,
			href: '/devices'
		},
		{
			name: $t('nav.global-vnc'),
			icon: ScreenShare,
			href: '/vnc',
			hidden: !anyTargetHasVNC
		},
		{
			name: $t('nav.history'),
			icon: GitBranch,
			href: '/history'
		},
		{
			name: $t('nav.external-repositories'),
			icon: Settings,
			href: '/external-repositories'
		},
		{
			name: $t('nav.secrets'),
			icon: FileLock,
			href: '/secrets'
		},
		{
			name: $t('nav.artifacts'),
			icon: FolderOpen,
			href: '/artifacts'
		}
	]);
</script>

<Sidebar
	class={drawerHidden ? 'hidden' : ''}
	{nonActiveClass}
	{activeClass}
	activeUrl={activeMainSidebar + $page.url.search}
	asideClass="{asideClass} lg:sticky lg:top-0 border-e border-gray-200 dark:border-gray-600 lg:block"
>
	<SidebarWrapper
		divClass="overflow-y-auto bg-white scrolling-touch h-full lg:block dark:bg-gray-800 lg:me-0"
	>
		<nav class="flex dark:divide-gray-600 text-base font-medium h-full">
			<SidebarGroup
				ulClass="list-unstyled fw-normal p-4  mt-2 lg:p-1 py-2 space-y-2 bg-gray-850 w-full"
			>
				{#each navItems as { name, icon, children, href, hidden } (name)}
					{#if !hidden}
						{@const SvelteComponent = icon}
						<a
							{href}
							lang={$locale}
							class={'flex flex-row lg:flex-col items-center text-center gap-2 text-xs hyphens-auto ' +
								(activeMainSidebar === href ? activeClass : nonActiveClass)}
						>
							<SvelteComponent size={20} />
							{name}
						</a>
					{/if}
				{/each}
			</SidebarGroup>
		</nav>
	</SidebarWrapper>
</Sidebar>
