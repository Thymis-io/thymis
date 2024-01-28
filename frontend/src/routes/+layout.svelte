<script lang="ts">
	import '../app.postcss';
	import {
		AppShell,
		AppRail,
		AppRailAnchor,
		AppBar,
		type ModalComponent
	} from '@skeletonlabs/skeleton';
	import {
		Grid2x2Icon,
		SettingsIcon,
		HistoryIcon,
		LayoutDashboard,
		Play,
		CloudCog
	} from 'lucide-svelte';
	import { page } from '$app/stores';
	import Logo from '$lib/Logo.svelte';
	import { Modal, initializeStores } from '@skeletonlabs/skeleton';
	import CreateDeviceModal from '$lib/CreateDeviceModal.svelte';
	import DeployModal from '$lib/DeployModal.svelte';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import { computePosition, autoUpdate, offset, shift, flip, arrow } from '@floating-ui/dom';
	import { storePopup, getModalStore } from '@skeletonlabs/skeleton';

	const modalRegistry: Record<string, ModalComponent> = {
		CreateDeviceModal: { ref: CreateDeviceModal },
		EditTagModal: { ref: EditTagModal },
		DeployModal: { ref: DeployModal }
	};

	initializeStores();
	storePopup.set({ computePosition, autoUpdate, offset, shift, flip, arrow });
	let modalStore = getModalStore();

	const build = async () => {
		await fetch('http://localhost:8000/action/build', { method: 'POST' });
	};

	const openDeploy = () => {
		modalStore.trigger({
			type: 'component',
			component: 'DeployModal',
			title: 'Deploy'
		});
	};
</script>

<Modal components={modalRegistry} />
<AppShell>
	<svelte:fragment slot="header">
		<AppBar>
			<svelte:fragment slot="lead"><Logo /></svelte:fragment>
			Thymis
			<svelte:fragment slot="trail">
				<button class="btn variant-filled" on:click={build}>
					<span><Play /></span><span>Build</span>
				</button>
				<button class="btn variant-filled" on:click={openDeploy}>
					<span><CloudCog /></span><span>Deploy</span>
				</button>
			</svelte:fragment>
		</AppBar>
	</svelte:fragment>
	<svelte:fragment slot="sidebarLeft">
		<AppRail>
			<svelte:fragment slot="lead">
				<AppRailAnchor href="/overview" selected={$page.url.pathname === '/overview'}>
					<svelte:fragment slot="lead"><LayoutDashboard /></svelte:fragment>
					<span>Overview</span>
				</AppRailAnchor>
			</svelte:fragment>
			<!-- --- -->
			<AppRailAnchor href="/modules" selected={$page.url.pathname === '/modules'} title="Modules">
				<svelte:fragment slot="lead"><Grid2x2Icon /></svelte:fragment>
				<span>Modules</span>
			</AppRailAnchor>
			<AppRailAnchor href="/history" selected={$page.url.pathname === '/history'} title="History">
				<svelte:fragment slot="lead"><HistoryIcon /></svelte:fragment>
				<span>History</span>
			</AppRailAnchor>
			<AppRailAnchor href="/config" selected={$page.url.pathname === '/config'} title="Config">
				<svelte:fragment slot="lead"><SettingsIcon /></svelte:fragment>
				<span>Config</span>
			</AppRailAnchor>
			<!-- --- -->
			<svelte:fragment slot="trail">
				<AppRailAnchor href="/account">
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
	<svelte:fragment slot="pageFooter">Page Footer</svelte:fragment>
	<!-- (footer) -->
</AppShell>
