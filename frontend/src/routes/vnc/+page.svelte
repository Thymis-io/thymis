<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { P, Card } from 'flowbite-svelte';
	import DeployActions from '$lib/DeployActions.svelte';

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<div />
	<DeployActions />
</div>
<div class="grid grid-cols-3 gap-4">
	{#each data.state.devices as device}
		<div>
			<P class="mb-2 text-center">{device.displayName}</P>
			<Card class="w-full max-w-none">
				<img alt="image" class="w-full aspect-video" />
			</Card>
		</div>
	{/each}
</div>
