<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { Button } from 'flowbite-svelte';
	import Pencil from 'lucide-svelte/icons/pencil';
	import CirclePlus from 'lucide-svelte/icons/circle-plus';
	import type { Device } from '$lib/state';
	import EditDeploymentInfo from '$lib/EditDeploymentInfo.svelte';

	export let deploymentInfos: DeploymentInfo[] = [];
	export let device: Device;

	let className = '';
	export { className as class };

	let editDeploymentInfoModalOpen = false;

	let currentDeploymentInfo: DeploymentInfo | undefined = deploymentInfos?.[0];
</script>

<EditDeploymentInfo
	bind:deploymentInfo={currentDeploymentInfo}
	bind:open={editDeploymentInfoModalOpen}
	configIdentifier={device.identifier}
/>
<Section class={className} title={$t('configuration-details.hostkey')}>
	<div class="flex flex-col gap-2">
		{#each deploymentInfos as deploymentInfo}
			{#if deploymentInfo}
				<div class="grid grid-cols-[max-content_1fr] gap-x-2">
					<p class="break-all text-base">{$t('configuration-details.targetHost')}:</p>
					<p class="break-all text-base">{deploymentInfo.reachable_deployed_host}</p>
					<p class="break-all text-base">{$t('configuration-details.publicKey')}:</p>
					<p class="break-all text-base">{deploymentInfo.ssh_public_key}</p>
				</div>
			{/if}
			<div class="flex flex-row gap-2">
				<Button
					size="sm"
					class="gap-2 p-2 py-1.5"
					color="alternative"
					on:click={() => {
						editDeploymentInfoModalOpen = true;
						currentDeploymentInfo = deploymentInfo;
					}}
				>
					<Pencil size={16} />
					<span class="text.-base">{$t('configuration-details.edit-hostkey')}</span>
				</Button>
			</div>
		{:else}
			<div class="flex flex-row gap-2">
				<Button
					size="sm"
					class="gap-2"
					color="alternative"
					on:click={() => {
						editDeploymentInfoModalOpen = true;
						currentDeploymentInfo = undefined;
					}}
				>
					<CirclePlus size={'1rem'} class="min-w-4" />
					<span>{$t('configuration-details.add-hostkey')}</span>
				</Button>
			</div>
		{/each}
	</div>
</Section>
