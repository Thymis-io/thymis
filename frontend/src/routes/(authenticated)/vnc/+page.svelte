<script lang="ts">
	import { t } from 'svelte-i18n';
	import { P } from 'flowbite-svelte';
	import { state } from '$lib/state';
	import VncView from '$lib/vnc/VncView.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import { browser } from '$app/environment';
	import type { PageData } from './$types';
	import PageHead from '$lib/components/PageHead.svelte';

	export let data: PageData;
</script>

<PageHead title={$t('nav.global-vnc')} />
<div class="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-4">
	{#each data.allDeploymentInfos as [configId, deploymentInfos]}
		{@const device = data.state.devices.find((d) => d.identifier === configId)}
		{#if device && targetShouldShowVNC(device, $state)}
			{#each deploymentInfos as deploymentInfo}
				<div class="">
					<p class=" mb-2 text-center text-gray-900 dark:text-white">{configId}</p>
					<VncView {device} {deploymentInfo} />
				</div>
			{/each}
		{/if}
	{/each}
</div>
