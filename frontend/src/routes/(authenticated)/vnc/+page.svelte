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
