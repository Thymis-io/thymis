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
		children?: Snippet;
		selectedDeploymentInfo?: DeploymentInfo | undefined;
	}

	let {
		nav,
		globalState,
		repoStatus,
		title,
		subtitle,
		children,
		selectedDeploymentInfo = undefined
	}: Props = $props();
</script>

<div class="ds-page-head">
	<div class="flex gap-4 items-center min-w-0">
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
	<DeployActions {repoStatus} {globalState} {nav} {selectedDeploymentInfo} />
</div>
