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
	import EditHostnameModal from '$lib/EditHostnameModal.svelte';

	import type { Icon } from 'lucide-svelte';
	import type { ComponentType } from 'svelte';
	import '../app.postcss';

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
	};

	const navItems: Array<NavItem> = [
		{ path: '/overview', text: $t('nav.overview'), icon: LayoutDashboard },
		{ path: '/config', text: $t('nav.orchestrate'), icon: CompassIcon },
		{ path: '/devices', text: $t('nav.devices'), icon: ServerIcon },
		{ path: '/history', text: $t('nav.history'), icon: HistoryIcon }
	];
</script>

<Modal components={modalRegistry} />
<AppShell>
	<svelte:fragment slot="header">
		<AppBar>
			<svelte:fragment slot="lead"><Logo /></svelte:fragment>
			<p class="text-xl font-bold">Thymis</p>
			<svelte:fragment slot="trail">
				<DeployActions />
			</svelte:fragment>
		</AppBar>
	</svelte:fragment>
	<svelte:fragment slot="sidebarLeft">
		<AppRail>
			{#each navItems as item, i}
				<AppRailAnchor href={item.path} selected={$page.url.pathname === item.path}>
					<svelte:fragment slot="lead">
						<svelte:component this={item.icon} />
					</svelte:fragment>
					<span>{item.text}</span>
				</AppRailAnchor>
			{/each}
			<svelte:fragment slot="trail">
				<AppRailAnchor href="/account" selected={$page.url.pathname === '/account'}>
					<svelte:fragment slot="lead">
						<svelte:component this={UserCog} />
					</svelte:fragment>
					<span>Account</span>
				</AppRailAnchor>
			</svelte:fragment>
		</AppRail>
	</svelte:fragment>
	<!-- (sidebarRight) -->
	<!-- (pageHeader) -->
	<!-- Router Slot -->
	<div class="m-8">
		<slot />
	</div>
	<!-- ---- / ---- -->
	<svelte:fragment slot="pageFooter" />
	<!-- (footer) -->
</AppShell>
