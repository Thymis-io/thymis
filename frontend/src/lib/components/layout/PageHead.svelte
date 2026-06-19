<script lang="ts">
	import DeployActions from '$lib/components/layout/DeployActions.svelte';
	import { page } from '$app/stores';
	import { type RepoStatus } from '$lib/repo/repo';
	import type { GlobalState } from '$lib/state.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import type { Snippet } from 'svelte';
	import type { Nav } from '../../../routes/(authenticated)/+layout';

	interface Props {
		title?: string;
		subtitle?: string;
		/** Title-adjacent content (badges, edit buttons) — rendered next to the title. */
		children?: Snippet;
		/** Page-level action buttons — rendered on the right, before the global deploy actions. */
		actions?: Snippet;
		selectedDeploymentInfo?: DeploymentInfo | undefined;
		/**
		 * The following come from the authenticated layout load and are read from
		 * `$page.data` automatically. Pass them only to override (rarely needed).
		 */
		nav?: Nav;
		globalState?: GlobalState;
		repoStatus?: RepoStatus;
	}

	let {
		title,
		subtitle,
		children,
		actions,
		selectedDeploymentInfo = undefined,
		nav,
		globalState,
		repoStatus
	}: Props = $props();

	// The authenticated layout load provides these; read them from the page store
	// so individual pages don't have to thread them through every <PageHead>.
	let layoutData = $derived(
		$page.data as { nav: Nav; globalState: GlobalState; repoStatus: RepoStatus }
	);
	let resolvedNav = $derived(nav ?? layoutData.nav);
	let resolvedGlobalState = $derived(globalState ?? layoutData.globalState);
	let resolvedRepoStatus = $derived(repoStatus ?? layoutData.repoStatus);
</script>

<div class="ds-page-head" data-testid="page-head">
	<div class="flex min-w-64 flex-1 items-center gap-4">
		{#if title}
			<div class="min-w-0">
				<h1 class="ds-page-title">{title}</h1>
				{#if subtitle}
					<p class="ds-page-subtitle">{subtitle}</p>
				{/if}
			</div>
		{/if}
		{@render children?.()}
	</div>
	<div class="flex flex-shrink-0 flex-wrap items-center justify-end gap-2">
		{@render actions?.()}
		<DeployActions
			repoStatus={resolvedRepoStatus}
			globalState={resolvedGlobalState}
			nav={resolvedNav}
			{selectedDeploymentInfo}
		/>
	</div>
</div>
