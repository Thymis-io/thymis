<script lang="ts">
	import type { PageData } from './$types';
	import { P, Card } from 'flowbite-svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { state } from '$lib/state';

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<div />
	<DeployActions />
</div>
<div class="grid grid-cols-3 gap-4">
	{#each $state.devices as device}
		<div>
			<P class="mb-2 text-center">{device.displayName}</P>
			<Card class="w-full max-w-none">
				<pre>vncviewer {device.targetHost}:5900</pre>
				<img alt=" " class="w-full aspect-video" />
			</Card>
		</div>
	{/each}
</div>
