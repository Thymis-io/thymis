<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { GlobalState } from '$lib/state.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import GitCommit from 'lucide-svelte/icons/git-commit-horizontal';
	import HeadTag from './HeadTag.svelte';
	import { type DeploymentInfo } from '$lib/deploymentInfo';

	export type ConfigInstance = {
		id: string;
		online: boolean;
		active: boolean;
		lastSeen: string | null;
		shortCommit: string | null;
		isCurrentCommit: boolean;
	};

	interface Props {
		inst: ConfigInstance;
		globalState: GlobalState;
		deploymentInfos: DeploymentInfo[];
	}

	let { inst, globalState, deploymentInfos }: Props = $props();
</script>

<div class="flex items-center w-full justify-between text-xs">
	<div class="flex items-center gap-2 w-full font-mono text-gray-600 dark:text-gray-300">
		<span
			class={[
				'h-2 w-2 flex-shrink-0 rounded-full',
				inst.online ? 'bg-emerald-500' : 'bg-gray-400'
			].join(' ')}
		></span>
		<div class="flex flex-col w-full">
			<IdentifierLink identifier={inst.id} context="device" {globalState} {deploymentInfos} />
			{#if inst.shortCommit}
				<div class="flex gap-1 items-center">
					<GitCommit size={'1rem'} class="flex-shrink-0" />
					<span class="font-mono text-gray-500 dark:text-gray-400">
						{inst.shortCommit}
						{#if inst.isCurrentCommit}
							<HeadTag />
						{/if}
					</span>
					{#if !inst.online}
						<span class="text-gray-400 dark:text-gray-500 ml-auto">
							{#if inst.lastSeen}
								<RenderTimeAgo timestamp={inst.lastSeen} />
							{:else}
								{$t('hardware-devices.table.never-seen')}
							{/if}
						</span>
					{/if}
				</div>
			{:else}
				<span class="text-gray-400">{$t('overview.no-commit')}</span>
			{/if}
		</div>
	</div>
</div>
