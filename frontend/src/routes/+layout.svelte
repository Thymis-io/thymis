<script lang="ts">
	import { page } from '$app/stores';
	import { t } from 'svelte-i18n';
	import CreateDeviceModal from '$lib/CreateDeviceModal.svelte';
	import DeployActions from '$lib/DeployActions.svelte';
	import DeployModal from '$lib/DeployModal.svelte';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import LogModal from '$lib/LogModal.svelte';
	import Logo from '$lib/Logo.svelte';
	import { arrow, autoUpdate, computePosition, flip, offset, shift } from '@floating-ui/dom';
	import { Sidebar, SidebarGroup, SidebarItem, SidebarWrapper } from 'flowbite-svelte';
	import {
		AppBar,
		AppRail,
		AppRailAnchor,
		AppShell,
		Modal,
		getModalStore,
		initializeStores,
		storePopup,
		type ModalComponent
	} from '@skeletonlabs/skeleton';
	// import {
	// 	Grid2x2Icon,
	// 	HistoryIcon,
	// 	LayoutDashboard,
	// 	SettingsIcon,
	// 	UserCog,
	// 	type Icon,
	// 	ServerIcon,
	// 	CompassIcon
	// } from 'lucide-svelte';
	import Grid2x2Icon from 'lucide-svelte/icons/grid-2x2';
	import HistoryIcon from 'lucide-svelte/icons/history';
	import LayoutDashboard from 'lucide-svelte/icons/layout-dashboard';
	import SettingsIcon from 'lucide-svelte/icons/settings';
	import UserCog from 'lucide-svelte/icons/user-cog';
	import ServerIcon from 'lucide-svelte/icons/server';
	import CompassIcon from 'lucide-svelte/icons/compass';
	import Terminal from 'lucide-svelte/icons/terminal';

	import EditHostnameModal from '$lib/EditHostnameModal.svelte';

	import type { Icon } from 'lucide-svelte';
	import { onMount, type ComponentType, SvelteComponent } from 'svelte';
	import '../app.postcss';
	import DeviceSelect from '$lib/DeviceSelect.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import { state } from '$lib/state';
	import BuildStatus from '$lib/BuildStatus.svelte';

	let ThymisEnterpriseHelloWorld: ComponentType<SvelteComponent> | null;
	onMount(async () => {
		// ThymisEnterpriseHelloWorld = (await import('../../node_modules/thymis-enterprise')).ThymisEnterpriseHelloWorld; // ENTERPRISEINCLUDE
		ThymisEnterpriseHelloWorld = null; // ENTERPRISEEXCLUDE
	});

	const tagParam = queryParam('tag');
	const deviceParam = queryParam('device');

	$: tag = $state?.tags.find((t) => t.name === $tagParam);
	$: device = $state?.devices.find((d) => d.hostname === $deviceParam);

	const modalRegistry: Record<string, ModalComponent> = {
		CreateDeviceModal: { ref: CreateDeviceModal },
		EditTagModal: { ref: EditTagModal },
		EditHostnameModal: { ref: EditHostnameModal },
		DeployModal: { ref: DeployModal },
		LogModal: { ref: LogModal }
	};

	initializeStores();
	storePopup.set({ computePosition, autoUpdate, offset, shift, flip, arrow });
	let modalStore = getModalStore();

	type NavItem = {
		path: string;
		text: string;
		icon: ComponentType<Icon>;
		hidden?: boolean;
	};

	let navItems: Array<NavItem>;
	$: navItems = [
		{ path: '/overview', text: $t('nav.overview'), icon: LayoutDashboard },
		{ path: '/config', text: $t('nav.orchestrate'), icon: CompassIcon },
		{ path: '/devices', text: $t('nav.devices'), icon: ServerIcon },
		{ path: '/history', text: $t('nav.history'), icon: HistoryIcon },
		{ path: '/terminal', text: $t('nav.terminal'), icon: Terminal, hidden: !device }
	];
	$: activeUrl = $page.url.pathname;
</script>

<Modal components={modalRegistry} />
<svelte:component this={ThymisEnterpriseHelloWorld} />
<AppShell>
	<svelte:fragment slot="header">
		<div class="bg-gradient-to-r from-blue-500 to-cyan-500">
			<div class="flex flex-wrap items-center justify-between px-4 py-2">
				<a href="https://flowbite.com/" class="flex items-center space-x-3 rtl:space-x-reverse">
					<Logo />
					<p class="text-xl font-bold text-white">Thymis Enterprise</p>
				</a>
				<button
					data-collapse-toggle="navbar-default"
					type="button"
					class="inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-500 rounded-lg md:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200 dark:text-gray-400 dark:hover:bg-gray-700 dark:focus:ring-gray-600"
					aria-controls="navbar-default"
					aria-expanded="false"
				>
					<span class="sr-only">Open main menu</span>
					<svg
						class="w-5 h-5"
						aria-hidden="true"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 17 14"
					>
						<path
							stroke="currentColor"
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M1 1h15M1 7h15M1 13h15"
						/>
					</svg>
				</button>
				<div class="hidden w-full md:block md:w-auto" id="navbar-default">
					<ul
						class="font-medium flex flex-col p-4 md:p-0 mt-4 border border-gray-100 rounded-lg bg-gray-50 md:flex-row md:space-x-8 rtl:space-x-reverse md:mt-0 md:border-0 md:bg-white dark:bg-gray-800 md:dark:bg-gray-900 dark:border-gray-700"
					>
						<li>
							<button class="btn">
								<span><UserCog /></span><span>Account</span>
							</button>
						</li>
					</ul>
				</div>
			</div>
		</div>
	</svelte:fragment>
	<svelte:fragment slot="sidebarLeft">
		<Sidebar {activeUrl}>
			<SidebarWrapper>
				<SidebarGroup>
					<DeviceSelect />
				</SidebarGroup>
				<SidebarGroup>
					{#each navItems as item, i}
						{#if !item.hidden}
							<SidebarItem label={item.text} href={item.path + $page.url.search}>
								<svelte:fragment slot="icon">
									<svelte:component this={item.icon} />
								</svelte:fragment>
							</SidebarItem>
						{/if}
					{/each}
				</SidebarGroup>
			</SidebarWrapper>
		</Sidebar>
		<BuildStatus/>
	</svelte:fragment>
	<!-- (sidebarRight) -->
	<!-- (pageHeader) -->
	<!-- Router Slot -->
	<div class="m-8 mt-4">
		<slot />
	</div>
	<!-- ---- / ---- -->
	<svelte:fragment slot="pageFooter" />
	<!-- (footer) -->
</AppShell>
