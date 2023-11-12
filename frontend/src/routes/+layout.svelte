<script lang="ts">
	import '../app.postcss';
	import { AppShell, AppRail, AppRailAnchor, AppBar } from '@skeletonlabs/skeleton';
	import { Grid2x2Icon, SettingsIcon, HistoryIcon } from 'lucide-svelte';
	import { page } from '$app/stores';
</script>

<AppShell>
	<svelte:fragment slot="header">
		<AppBar>
			<svelte:fragment slot="lead">(icon)</svelte:fragment>
			Thymis
			<svelte:fragment slot="trail">(actions)</svelte:fragment>
		</AppBar>
	</svelte:fragment>
	<svelte:fragment slot="sidebarLeft">
		<AppRail>
			<svelte:fragment slot="lead">
				<AppRailAnchor href="/">
					<svelte:fragment slot="lead">(icon)</svelte:fragment>
					<span>Thymis</span>
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
