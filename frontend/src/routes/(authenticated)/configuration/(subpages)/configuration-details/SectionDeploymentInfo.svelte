<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import type { DeploymentInfo } from '$lib/deploymentInfo';
	import { isOnline, isActive } from '$lib/deploymentInfo';
	import type { GlobalState } from '$lib/state.svelte';
	import DeploymentInstanceRow, {
		type ConfigInstance
	} from '$lib/components/DeploymentInstanceRow.svelte';

	interface Props {
		deploymentInfos?: DeploymentInfo[];
		globalState: GlobalState;
		headCommit?: string | null;
		class?: string;
	}

	let {
		deploymentInfos = [],
		globalState,
		headCommit = null,
		class: className = ''
	}: Props = $props();

	// Normalise HEAD to 7-char short hash so comparisons are consistent
	// regardless of whether the caller supplies a full SHA1 or a short hash.
	let shortHead = $derived(headCommit?.slice(0, 7) ?? null);

	let instances: ConfigInstance[] = $derived(
		deploymentInfos
			.filter((di) => isActive(di.last_seen) || isOnline(di.last_seen))
			.map((di) => {
				const shortCommit = di.deployed_config_commit?.slice(0, 7) ?? null;
				return {
					id: di.id,
					online: isOnline(di.last_seen),
					active: isActive(di.last_seen),
					lastSeen: di.last_seen,
					shortCommit,
					isCurrentCommit: !!shortCommit && shortCommit === shortHead
				};
			})
			.sort((a, b) => Number(b.online) - Number(a.online))
	);
</script>

<Section class={className} title={$t('configuration-details.deployment-info')}>
	<div class="flex flex-col gap-2 max-w-96">
		{#each instances as inst (inst.id)}
			<DeploymentInstanceRow {inst} {globalState} {deploymentInfos} />
		{/each}
	</div>
</Section>
