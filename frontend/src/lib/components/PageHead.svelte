<script lang="ts">
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { type RepoStatus } from '$lib/repo/repo';

	export let repoStatus: RepoStatus;
	export let title: string;
</script>

<div class="flex justify-between mb-4">
	<div class="flex gap-4">
		<h1 class="text-3xl font-bold dark:text-white">{title}</h1>
		<slot />
	</div>
	<DeployActions {repoStatus} />
</div>
