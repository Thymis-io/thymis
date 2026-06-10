<script lang="ts">
	import DeployActions from '$lib/components/layout/DeployActions.svelte';
	import { type RepoStatus } from '$lib/repo/repo';
	import type { GlobalState } from '$lib/state.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import type { Snippet } from 'svelte';
	import type { Nav } from '../../../routes/(authenticated)/+layout';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		repoStatus: RepoStatus;
		title?: string;
		subtitle?: string;
		/** Title-adjacent content (badges, edit buttons) — rendered next to the title. */
		children?: Snippet;
		/** Page-level action buttons — rendered on the right, before the global deploy actions. */
		actions?: Snippet;
		selectedDeploymentInfo?: DeploymentInfo | undefined;
	}

	let {
		nav,
		globalState,
		repoStatus,
		title,
		subtitle,
		children,
		actions,
		selectedDeploymentInfo = undefined
	}: Props = $props();
</script>

<div class="ds-page-head">
	<div class="flex min-w-0 flex-1 items-center gap-4">
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
		<DeployActions {repoStatus} {globalState} {nav} {selectedDeploymentInfo} />
	</div>
</div>
