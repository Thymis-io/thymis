<script lang="ts">
	import type { PageData } from './$types';
	import { P } from 'flowbite-svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { state, type Device } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';

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
			<VncView {device} />
		</div>
	{/each}
</div>
