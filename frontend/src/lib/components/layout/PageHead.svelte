<script lang="ts">
	import DeployActions from '$lib/components/layout/DeployActions.svelte';
	import { type RepoStatus } from '$lib/repo/repo';

	interface Props {
		repoStatus: RepoStatus;
		title: string;
		children?: import('svelte').Snippet;
	}

	let { repoStatus, title, children }: Props = $props();
</script>

<div class="flex justify-between mb-4">
	<div class="flex gap-4">
		<h1 class="text-3xl font-bold dark:text-white">{title}</h1>
		{@render children?.()}
	</div>
	<DeployActions {repoStatus} />
</div>
