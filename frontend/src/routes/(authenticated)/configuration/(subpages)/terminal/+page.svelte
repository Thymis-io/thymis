<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import type { PageData } from './$types';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import Copy from 'lucide-svelte/icons/copy';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
	// one Terminal instance per connected device so each card header can trigger
	// that device's "Copy SSH Command".
	let terminalRefs = $state<Record<string, Terminal>>({});
</script>

{#if data.connectedDeploymentInfos.length === 0}
	<div class="ds-card ds-table-empty">{$t('configuration-details.no-deployment-info')}</div>
{:else}
	<div class="flex flex-col gap-4">
		{#each data.connectedDeploymentInfos as deploymentInfo}
			<div class="ds-card flex flex-col">
				<div class="ds-card-head">
					<IdentifierLink
						globalState={data.globalState}
						deploymentInfos={data.deploymentInfos}
						identifier={deploymentInfo.id}
						context="device"
					/>
					<button
						class="ds-btn ds-btn-sm ds-btn-primary flex items-center gap-2"
						onclick={() => terminalRefs[deploymentInfo.id]?.copySSHCommand()}
					>
						<Copy size={15} />
						<span class="whitespace-nowrap">Copy SSH Command</span>
					</button>
				</div>
				<div class="ds-card-pad">
					<Terminal bind:this={terminalRefs[deploymentInfo.id]} {deploymentInfo} />
				</div>
			</div>
		{/each}
	</div>
{/if}
