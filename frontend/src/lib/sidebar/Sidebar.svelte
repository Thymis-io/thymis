<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { t } from 'svelte-i18n';
	import { Sidebar, SidebarGroup, SidebarWrapper } from 'flowbite-svelte';
	import ServerSolid from 'svelte-awesome-icons/ServerSolid.svelte';
	import CodeCommitSolid from 'svelte-awesome-icons/CodeCommitSolid.svelte';
	import ChartSimpleSolid from 'svelte-awesome-icons/ChartSimpleSolid.svelte';
	import GearSolid from 'svelte-awesome-icons/GearSolid.svelte';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import { state } from '$lib/state';
	import GlobalNavSelect from '$lib/sidebar/GlobalNavSelect.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

	export let drawerHidden: boolean;

	const closeDrawer = () => {
		drawerHidden = true;
	};

	let spanClass = 'ms-4';
	let childClass =
		'p-1 hover:bg-gray-100 text-gray-500 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200 ';

	let nonActiveClass =
		childClass + ' hover:cursor-pointer dark:text-gray-400 hover:text-black dark:hover:text-white';
	let activeClass = childClass + ' cursor-default text-primary-600 dark:text-primary-400';
	export let asideClass = '';

	$: mainSidebarUrl = $page.url.pathname;
	let activeMainSidebar: string;

	afterNavigate((navigation) => {
		// this fixes https://github.com/themesberg/flowbite-svelte/issues/364
		document.getElementById('svelte')?.scrollTo({ top: 0 });
		closeDrawer();

		activeMainSidebar = navigation.to?.url.pathname ?? '';

		// const key = fileDir(activeMainSidebar);
		// for (const k in dropdowns) dropdowns[k] = false;
		// dropdowns[key] = true;
	});

	type NavItem = {
		name: string;
		icon: any;
		href: string;
		hidden?: boolean;
		children?: Record<string, string>;
	};

	$: anyTargetHasVNC =
		$state.configs.some((config) => targetShouldShowVNC(config, $state)) ||
		$state.tags.some((tag) => targetShouldShowVNC(tag, $state));

	let navItems: NavItem[] = [];
	$: navItems = [
		{
			name: $t('nav.overview'),
			icon: ChartSimpleSolid,
			href: '/overview'
		},
		{
			name: $t('nav.configurations'),
			icon: FileCode,
			href: '/configuration/list'
		},
		{
			name: $t('nav.devices'),
			icon: ServerSolid,
			href: '/devices'
		},
		{
			name: $t('nav.tags'),
			icon: TagIcon,
			href: '/tags'
		},
		{
			name: $t('nav.global-vnc'),
			icon: ScreenShare,
			href: '/vnc',
			hidden: !anyTargetHasVNC
		},
		{
			name: $t('nav.history'),
			icon: CodeCommitSolid,
			href: '/history'
		},
		{
			name: $t('nav.external-repositories'),
			icon: GearSolid,
			href: '/external-repositories'
		}
	];

	let dropdowns = Object.fromEntries(Object.keys(navItems).map((x) => [x, false]));
</script>

<Sidebar
	class={drawerHidden ? 'hidden' : ''}
	{nonActiveClass}
	{activeClass}
	activeUrl={activeMainSidebar + $page.url.search}
	asideClass="{asideClass} lg:sticky lg:top-0 border-e border-gray-200 dark:border-gray-600 lg:block"
>
	<SidebarWrapper
		divClass="overflow-y-auto  bg-white scrolling-touch h-full lg:block dark:bg-gray-800 lg:me-0"
	>
		<nav class="flex divide-x divide-gray-200 dark:divide-gray-600 text-base font-medium h-full">
			<SidebarGroup ulClass="list-unstyled fw-normal p-1 py-2 space-y-2 bg-gray-850">
				{#each navItems as { name, icon, children, href, hidden } (name)}
					{#if !hidden}
						<a
							{href}
							class={'flex flex-col items-center text-center gap-2 text-xs w-16 ' +
								(activeMainSidebar === href ? activeClass : nonActiveClass)}
						>
							<svelte:component this={icon} size={20} />
							{name}
						</a>
					{/if}
				{/each}
			</SidebarGroup>
			<div class="flex flex-col p-2 w-full overflow-x-auto">
				<GlobalNavSelect />
			</div>
		</nav>
	</SidebarWrapper>
</Sidebar>
