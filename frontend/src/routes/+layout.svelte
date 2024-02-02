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
	import CreateDeviceModal from '$lib/CreateDeviceModal.svelte';
	import DeployModal from '$lib/DeployModal.svelte';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import LogModal from '$lib/LogModal.svelte';
	import { computePosition, autoUpdate, offset, shift, flip, arrow } from '@floating-ui/dom';
	import {
		Modal,
		initializeStores,
		popup,
		storePopup,
		getModalStore,
		type PopupSettings
	} from '@skeletonlabs/skeleton';
	import { buildStatus } from '$lib/buildstatus';
	import { Info, AlertTriangle } from 'lucide-svelte';

	const modalRegistry: Record<string, ModalComponent> = {
		CreateDeviceModal: { ref: CreateDeviceModal },
		EditTagModal: { ref: EditTagModal },
		DeployModal: { ref: DeployModal },
		LogModal: { ref: LogModal }
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

	function openStdoutModal() {
		modalStore.trigger({
			type: 'component',
			component: 'LogModal',
			title: 'Stdout',
			meta: { log: $buildStatus?.stdout }
		});
	}

	function openStderrModal() {
		modalStore.trigger({
			type: 'component',
			component: 'LogModal',
			title: 'Stderr',
			meta: { log: $buildStatus?.stderr }
		});
	}

	const stdoutPopupHover: PopupSettings = {
		event: 'hover',
		target: 'stdoutPopup',
		placement: 'top'
	};

	const stderrPopupHover: PopupSettings = {
		event: 'hover',
		target: 'stderrPopup',
		placement: 'top'
	};
</script>

<Modal components={modalRegistry} />
<AppShell>
	<svelte:fragment slot="header">
		<AppBar>
			<svelte:fragment slot="lead"><Logo /></svelte:fragment>
			Thymis
			<svelte:fragment slot="trail">
				<span>
					Build Status: {$buildStatus?.status}
				</span>
				{#if $buildStatus?.stdout}
					<div class="mt-1.5 ml-2">
						<button
							class="btn p-0 [&>*]:pointer-events-none"
							use:popup={stdoutPopupHover}
							on:click={openStdoutModal}
						>
							<Info color="#0080c0" />
						</button>
						<div class="card p-4 variant-filled-primary z-40" data-popup="stdoutPopup">
							<pre>{$buildStatus?.stdout}</pre>
							<div class="arrow variant-filled-primary" />
						</div>
					</div>
				{/if}
				{#if $buildStatus?.stderr}
					<div class="mt-1.5 ml-2">
						<button
							class="btn p-0 [&>*]:pointer-events-none"
							use:popup={stderrPopupHover}
							on:click={openStderrModal}
						>
							<AlertTriangle color="#c4c400" />
						</button>
						<div class="card p-4 variant-filled-primary z-40" data-popup="stderrPopup">
							<pre>{$buildStatus?.stderr}</pre>
							<div class="arrow variant-filled-primary" />
						</div>
					</div>
				{/if}
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
