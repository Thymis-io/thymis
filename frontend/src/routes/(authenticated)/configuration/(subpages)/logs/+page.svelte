<script lang="ts">
	import { queryParameters } from 'sveltekit-search-params';
	import type { PageData } from './$types';
	import LogsView from '$lib/components/LogsView.svelte';

	interface Props {
		data: PageData;
	}

	let { data }: Props = $props();

	const params = queryParameters();
	let selectedDeploymentInfoId = $derived.by(() => params['deployment-info-id']);
</script>

<LogsView
	globalState={data.globalState}
	logs={data.logs}
	programNames={data.programNames}
	deploymentInfos={data.deploymentInfos}
	connectedDeploymentInfos={data.connectedDeploymentInfos}
	{selectedDeploymentInfoId}
	showSelector={true}
	onSelectDeploymentInfo={(id) => (params['deployment-info-id'] = id)}
/>
