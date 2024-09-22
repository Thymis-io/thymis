<script lang="ts">
	import type { PageData } from './$types';
	import { P } from 'flowbite-svelte';
	import {
		globalNavSelectedDevice,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<div />
	<DeployActions />
</div>
{#if $globalNavSelectedTargetType === 'device' && $globalNavSelectedDevice}
	<p>Test</p>
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			<p>Test</p>
		{/each}
	</div>
{/if}
