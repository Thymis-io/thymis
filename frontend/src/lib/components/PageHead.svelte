<script lang="ts">
	import DeployActions from '$lib/components/DeployActions.svelte';

	export let title: string;
</script>

<div class="flex justify-between mb-4">
	<div class="flex gap-4">
		<h1 class="text-3xl font-bold dark:text-white">{title}</h1>
		<slot />
	</div>
	<DeployActions />
</div>
