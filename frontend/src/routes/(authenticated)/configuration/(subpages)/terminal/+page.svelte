<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import { globalNavSelectedConfig, globalNavSelectedTarget } from '$lib/state';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import type { PageData } from './$types';
	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();
</script>

{#if data.deploymentInfos}
	{#each data.deploymentInfos as deploymentInfo}
		<Terminal {deploymentInfo} />
	{/each}
{/if}
