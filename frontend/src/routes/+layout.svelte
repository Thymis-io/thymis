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
	import type { ComponentType } from 'svelte';
	import '../app.postcss';
	import DeviceSelect from '$lib/DeviceSelect.svelte';
	import { queryParam } from 'sveltekit-search-params';
	import { state } from '$lib/state';
	import BuildStatus from '$lib/BuildStatus.svelte';

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
</script>

<Modal components={modalRegistry} />
<AppShell>
	<svelte:fragment slot="header">
		<AppBar background="bg-gradient-to-r from-blue-500 to-cyan-500" padding="px-4 py-2">
			<svelte:fragment slot="lead"><Logo /></svelte:fragment>
			<p class="text-xl font-bold text-white">Thymis Enterprise</p>
			<svelte:fragment slot="trail">
				<button class="btn">
					<span><UserCog /></span><span>Account</span>
				</button>
			</svelte:fragment>
		</AppBar>
	</svelte:fragment>
	<svelte:fragment slot="sidebarLeft">
		<AppRail width="w-60" aspectRatio="aspect-[8/2]" background="bg-surface" active="rounded-r-lg bg-primary-active-token">
			<AppRailAnchor regionLead="px-2">
				<svelte:fragment slot="lead">
					<DeviceSelect />
				</svelte:fragment>
			</AppRailAnchor>
			{#each navItems as item, i}
				{#if !item.hidden}
					<AppRailAnchor
						regionLead="flex flex-row pl-4 gap-2 items-center"
						href={item.path + $page.url.search}
						selected={$page.url.pathname === item.path}
					>
						<svelte:fragment slot="lead">
							<svelte:component this={item.icon} />
							<span>{item.text}</span>
						</svelte:fragment>
					</AppRailAnchor>
				{/if}
			{/each}
			<svelte:fragment slot="trail">
				<AppRailAnchor>
					<svelte:fragment slot="lead">
						<BuildStatus />
					</svelte:fragment>
				</AppRailAnchor>
			</svelte:fragment>
		</AppRail>
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
