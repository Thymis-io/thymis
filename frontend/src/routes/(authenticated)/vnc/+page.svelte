<script lang="ts">
	import { t } from 'svelte-i18n';
	import { P } from 'flowbite-svelte';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import { state } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import { getDeploymentInfosByConfigId } from '$lib/deploymentInfo';
	import { browser } from '$app/environment';
	import type { PageData } from './$types';
	export let data: PageData;
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">{$t('nav.global-vnc')}</h1>
	<DeployActions />
</div>
<div class="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-4">
	{#each $state.devices as device}
		{#if targetShouldShowVNC(device, $state)}
			<div>
				<P class="mb-2 text-center">{device.displayName}</P>
				{#if browser}
					{#each data.allDeploymentInfos.get(device.identifier) ?? [] as deploymentInfo}
						<VncView {device} {deploymentInfo} />
					{/each}
				{/if}
			</div>
		{/if}
	{/each}
</div>
