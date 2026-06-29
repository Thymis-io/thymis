<script lang="ts">
	import LogsView from '$lib/components/LogsView.svelte';
	import type { PageData } from './$types';

	interface Props {
		data: PageData;
	}
	let { data }: Props = $props();

	let deploymentInfo = $derived(
		data.globalState.deploymentInfos.find((di) => di.id === data.deploymentInfoId)!
	);
</script>

<LogsView
	globalState={data.globalState}
	logs={data.logs}
	programNames={data.programNames}
	connectedDeploymentInfos={deploymentInfo.connected ? [deploymentInfo] : []}
	selectedDeploymentInfoId={deploymentInfo.id}
	showSelector={false}
/>
