<script lang="ts">
	import { page } from '$app/stores';
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
		initializeStores, storePopup,
		type ModalComponent
	} from '@skeletonlabs/skeleton';
	import {
		Grid2x2Icon,
		HistoryIcon,
		LayoutDashboard,
		SettingsIcon,
		UserCog,
		type Icon
	} from 'lucide-svelte';
	import type { ComponentType } from 'svelte';
	import '../app.postcss';

	const modalRegistry: Record<string, ModalComponent> = {
		CreateDeviceModal: { ref: CreateDeviceModal },
		EditTagModal: { ref: EditTagModal },
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
		{ path: '/overview', text: 'Overview', icon: LayoutDashboard },
		{ path: '/modules', text: 'Modules', icon: Grid2x2Icon },
		{ path: '/history', text: 'History', icon: HistoryIcon },
		{ path: '/config', text: 'Config', icon: SettingsIcon }
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
