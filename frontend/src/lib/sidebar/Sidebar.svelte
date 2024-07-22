<script lang="ts">
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { t } from 'svelte-i18n';

	import {
		Sidebar,
		SidebarDropdownWrapper,
		SidebarGroup,
		SidebarItem,
		SidebarWrapper
	} from 'flowbite-svelte';
	import AngleDownOutline from 'flowbite-svelte-icons/AngleDownOutline.svelte';
	import AngleUpOutline from 'flowbite-svelte-icons/AngleUpOutline.svelte';
	import ServerSolid from 'svelte-awesome-icons/ServerSolid.svelte';
	import SlidersSolid from 'svelte-awesome-icons/SlidersSolid.svelte';
	import CodeCommitSolid from 'svelte-awesome-icons/CodeCommitSolid.svelte';
	import TerminalSolid from 'svelte-awesome-icons/TerminalSolid.svelte';
	import ChartSimpleSolid from 'svelte-awesome-icons/ChartSimpleSolid.svelte';
	import GearSolid from 'svelte-awesome-icons/GearSolid.svelte';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import {
		globalNavSelectedDevice,
		globalNavSelectedTarget,
		globalNavSelectedTargetType,
		state,
		type ModuleSettings
	} from '$lib/state';
	import BuildStatus from '$lib/sidebar/BuildStatus.svelte';
	import GlobalNavSelect from '$lib/sidebar/GlobalNavSelect.svelte';

	export let drawerHidden: boolean;

	const closeDrawer = () => {
		drawerHidden = true;
	};

	let spanClass = 'ms-9';
	let childClass =
		'p-2 hover:bg-gray-100 text-gray-500 dark:hover:bg-gray-700 rounded-lg transition-colors duration-200 relative flex items-center flex-wrap font-medium';

	let nonActiveClass =
		childClass +
		' hover:text-gray-500 hover:cursor-pointer dark:text-gray-400 dark:hover:text-white';
	let activeClass = childClass + ' cursor-default text-primary-600 dark:text-primary-400';

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

	const isVNCModule = (module: ModuleSettings) => module.type.toLowerCase().includes('vnc');

	$: hasVNCModule =
		$state.devices.some((device) => device.modules.some(isVNCModule)) ||
		$state.tags.some((tag) => tag.modules.some(isVNCModule));

	let dynamicNavItems: NavItem[] = [];
	$: dynamicNavItems = [
		{
			name: $t(`nav.config-${$globalNavSelectedTargetType}`),
			icon: SlidersSolid,
			href: '/config',
			hidden: !$globalNavSelectedTarget
		},
		{
			name: $t('nav.terminal'),
			icon: TerminalSolid,
			href: '/terminal',
			hidden: !$globalNavSelectedDevice
		}
	];

	let navItems: NavItem[] = [];
	$: navItems = [
		{
			name: $t('nav.overview'),
			icon: ChartSimpleSolid,
			href: '/overview'
		},
		{
			name: $t('nav.devices'),
			icon: ServerSolid,
			href: '/devices'
		},
		{
			name: $t('nav.vnc'),
			icon: ScreenShare,
			href: '/vnc',
			hidden: !hasVNCModule
		},
		{
			name: $t('nav.history'),
			icon: CodeCommitSolid,
			href: '/history'
		},
		{
			name: $t('nav.settings'),
			icon: GearSolid,
			href: '/settings'
		}
	];

	let dropdowns = Object.fromEntries(Object.keys(navItems).map((x) => [x, false]));
</script>

<Sidebar
	class={drawerHidden ? 'hidden' : ''}
	{nonActiveClass}
	{activeClass}
	activeUrl={activeMainSidebar + $page.url.search}
	asideClass="fixed inset-0 z-30 flex-none h-full w-64 lg:h-auto border-e border-gray-200 dark:border-gray-600 lg:overflow-y-visible lg:pt-20 lg:-mt-2 lg:block"
>
	<SidebarWrapper
		divClass="overflow-y-auto px-4 pt-20 lg:pt-4 h-full bg-white scrolling-touch max-w-2xs lg:h-[calc(100vh-4.5rem)] lg:block dark:bg-gray-800 lg:me-0 lg:sticky top-2"
	>
		<nav class="divide-y text-base font-medium">
			<SidebarGroup ulClass="list-unstyled fw-normal small mb-4 space-y-2">
				<GlobalNavSelect />
				{#each navItems as { name, icon, children, href, hidden } (name)}
					{#if children}
						<SidebarDropdownWrapper
							bind:isOpen={dropdowns[name]}
							label={name}
							ulClass="mt-0.5"
							btnClass="flex p-2 rounded-lg items-center justify-start gap-4 w-full text-base font-medium tracking-wide hover:text-primary-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
							spanClass=""
							class={dropdowns[name]
								? 'text-primary-700 dark:text-white'
								: 'text-gray-500 dark:text-gray-400'}
						>
							<AngleDownOutline slot="arrowdown" class="ms-auto text-gray-800 dark:text-white" />
							<AngleUpOutline slot="arrowup" class="ms-auto text-gray-800 dark:text-white" />
							<svelte:component this={icon} slot="icon" />
							{#each Object.entries(children) as [title, href]}
								<SidebarItem
									label={title}
									href={href + $page.url.search}
									{spanClass}
									{activeClass}
								/>
							{/each}
						</SidebarDropdownWrapper>
					{:else if !hidden}
						<SidebarItem label={name} href={href + $page.url.search} {spanClass} {activeClass}>
							<svelte:component this={icon} slot="icon" size={18} />
						</SidebarItem>
					{/if}
				{/each}
				<hr />
				{#each dynamicNavItems as { name, icon, children, href, hidden } (name)}
					{#if children}
						<SidebarDropdownWrapper
							bind:isOpen={dropdowns[name]}
							label={name}
							ulClass="mt-0.5"
							btnClass="flex p-2 rounded-lg items-center justify-start gap-4 w-full text-base font-medium tracking-wide hover:text-primary-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
							spanClass=""
							class={dropdowns[name]
								? 'text-primary-700 dark:text-white'
								: 'text-gray-500 dark:text-gray-400'}
						>
							<AngleDownOutline slot="arrowdown" class="ms-auto text-gray-800 dark:text-white" />
							<AngleUpOutline slot="arrowup" class="ms-auto text-gray-800 dark:text-white" />
							<svelte:component this={icon} slot="icon" />
							{#each Object.entries(children) as [title, href]}
								<SidebarItem
									label={title}
									href={href + $page.url.search}
									{spanClass}
									{activeClass}
								/>
							{/each}
						</SidebarDropdownWrapper>
					{:else if !hidden}
						<SidebarItem label={name} href={href + $page.url.search} {spanClass} {activeClass}>
							<svelte:component this={icon} slot="icon" size={18} />
						</SidebarItem>
					{/if}
				{/each}
			</SidebarGroup>
			<SidebarGroup ulClass="list-unstyled fw-normal small p-2 pt-4 space-y-2">
				<BuildStatus />
			</SidebarGroup>
		</nav>
	</SidebarWrapper>
</Sidebar>

<div
	hidden={drawerHidden}
	class="fixed inset-0 z-20 bg-gray-900/50 dark:bg-gray-900/60 lg:hidden"
	on:click={closeDrawer}
	on:keydown={closeDrawer}
	role="presentation"
/>
