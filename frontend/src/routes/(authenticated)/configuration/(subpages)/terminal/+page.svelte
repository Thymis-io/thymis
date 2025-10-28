<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

{#if data.connectedDeploymentInfos}
	{#each data.connectedDeploymentInfos as deploymentInfo}
		<Terminal {deploymentInfo} />
	{/each}
{/if}
