<script lang="ts">
	import type { PageData } from './$types';
	import { P } from 'flowbite-svelte';
	import {
		globalNavSelectedDevice,
		globalNavSelectedTag,
		globalNavSelectedTargetType
	} from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';

	export let data: PageData;
</script>

{#if $globalNavSelectedTargetType === 'device' && $globalNavSelectedDevice}
	<VncView device={$globalNavSelectedDevice} />
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			<div>
				<P class="mb-2 text-center">{device.displayName}</P>
				<VncView {device} />
			</div>
		{/each}
	</div>
{/if}
