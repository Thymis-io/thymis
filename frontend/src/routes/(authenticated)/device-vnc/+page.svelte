<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { P } from 'flowbite-svelte';
	import {
		globalNavSelectedDevice,
		globalNavSelectedTag,
		globalNavSelectedTarget,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import Tabbar from '$lib/components/Tabbar.svelte';

	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">{$globalNavSelectedTarget?.displayName}</h1>
	<DeployActions />
</div>
<Tabbar />
{#if $globalNavSelectedTargetType === 'device' && $globalNavSelectedDevice}
	<VncView device={$globalNavSelectedDevice} />
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			{#if targetShouldShowVNC(device, $state)}
				<div>
					<P class="mb-2 text-center">{device.displayName}</P>
					<VncView {device} />
				</div>
			{/if}
		{/each}
	</div>
{/if}
