<script lang="ts">
	import { AppShell, AppRail, AppRailTile, AppRailAnchor, AppBar } from '@skeletonlabs/skeleton';
	import Modules from '$lib/Modules.svelte';
	import History from '$lib/History.svelte';
	import Config from '$lib/Config.svelte';
	let currentTile: number = 0;
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
				<AppRailAnchor href="/">(icon)</AppRailAnchor>
			</svelte:fragment>
			<!-- --- -->
			<AppRailTile bind:group={currentTile} name="tile-1" value={0} title="tile-1">
				<svelte:fragment slot="lead">(icon)</svelte:fragment>
				<span>Tile 1</span>
			</AppRailTile>
			<AppRailTile bind:group={currentTile} name="tile-2" value={1} title="tile-2">
				<svelte:fragment slot="lead">(icon)</svelte:fragment>
				<span>Tile 2</span>
			</AppRailTile>
			<AppRailTile bind:group={currentTile} name="tile-3" value={2} title="tile-3">
				<svelte:fragment slot="lead">(icon)</svelte:fragment>
				<span>Tile 3</span>
			</AppRailTile>
			<!-- --- -->
			<svelte:fragment slot="trail">
				<AppRailAnchor href="/" target="_blank" title="Account">(icon)</AppRailAnchor>
			</svelte:fragment>
		</AppRail>
	</svelte:fragment>
	<!-- (sidebarRight) -->
	<!-- (pageHeader) -->
	<!-- Router Slot -->
	<slot />
	<div class="m-8">
		{#if currentTile === 0}
			<Modules />
		{/if}
		{#if currentTile === 1}
			<History />
		{/if}
		{#if currentTile === 2}
			<Config />
		{/if}
	</div>
	<!-- ---- / ---- -->
	<svelte:fragment slot="pageFooter">Page Footer</svelte:fragment>
	<!-- (footer) -->
</AppShell>
