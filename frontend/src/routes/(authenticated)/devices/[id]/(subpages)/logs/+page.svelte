<script lang="ts">
	import LogsView from '$lib/components/LogsView.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $derived(data.deploymentInfo);
</script>

<LogsView
	globalState={data.globalState}
	logs={data.logs}
	programNames={data.programNames}
	deploymentInfos={[deploymentInfo]}
	connectedDeploymentInfos={data.connected ? [deploymentInfo] : []}
	selectedDeploymentInfoId={deploymentInfo.id}
	showSelector={false}
/>
