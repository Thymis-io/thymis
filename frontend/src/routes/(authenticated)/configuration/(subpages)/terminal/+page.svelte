<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import CopySSHCommandButton from '$lib/terminal/CopySSHCommandButton.svelte';
	import type { PageData } from './$types';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

{#if data.deploymentInfos.filter((d) => d.connected).length === 0}
	<div class="ds-card ds-table-empty">{$t('configuration-details.no-deployment-info')}</div>
{:else}
	<div class="flex flex-col gap-4">
		{#each data.deploymentInfos.filter((d) => d.connected) as deploymentInfo}
			<div class="ds-card flex flex-col">
				<div class="ds-card-head">
					<IdentifierLink
						globalState={data.globalState}
						identifier={deploymentInfo.id}
						context="device"
					/>
					<CopySSHCommandButton {deploymentInfo} />
				</div>
				<div class="ds-card-pad">
					<Terminal {deploymentInfo} />
				</div>
			</div>
		{/each}
	</div>
{/if}
