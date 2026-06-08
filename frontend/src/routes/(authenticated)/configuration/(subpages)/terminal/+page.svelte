<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import type { PageData } from './$types';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import { Card } from 'flowbite-svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

{#if data.connectedDeploymentInfos}
	{#each data.connectedDeploymentInfos as deploymentInfo}
		<div>
			<IdentifierLink
				globalState={data.globalState}
				deploymentInfos={data.deploymentInfos}
				identifier={deploymentInfo.id}
				context="device"
				class="flex justify-center my-2"
			/>
			<Card class="w-full max-w-none" padding="sm">
				<Terminal {deploymentInfo} />
			</Card>
		</div>
	{/each}
{/if}
