<script lang="ts">
	import DeployActions from '$lib/components/layout/DeployActions.svelte';
	import { type RepoStatus } from '$lib/repo/repo';
	import type { GlobalState } from '$lib/state.svelte';
	import type { Snippet } from 'svelte';
	import type { Nav } from '../../../routes/(authenticated)/+layout';

	interface Props {
		nav: Nav;
		globalState: GlobalState;
		repoStatus: RepoStatus;
		title?: string;
		children?: Snippet;
	}

	let { nav, globalState, repoStatus, title, children }: Props = $props();
</script>

<div class="flex justify-between mb-4">
	<div class="flex gap-4">
		{#if title}
			<h1 class="text-3xl font-bold dark:text-white">{title}</h1>
		{/if}
		{@render children?.()}
	</div>
	<DeployActions {repoStatus} {globalState} {nav} />
</div>
