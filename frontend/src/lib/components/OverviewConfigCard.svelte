<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card } from 'flowbite-svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import RenderTimeAgo from '$lib/components/RenderTimeAgo.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';
	import GitCommit from 'lucide-svelte/icons/git-commit-horizontal';
	import HeadTag from './HeadTag.svelte';

	type ConfigInstance = {
		id: string;
		online: boolean;
		active: boolean;
		lastSeen: string | null;
		shortCommit: string | null;
		isCurrentCommit: boolean;
	};

	type ConfigCard = {
		identifier: string;
		displayName: string;
		deviceTypeLabel: string;
		activeInstances: ConfigInstance[];
		onlineCount: number;
	};

	interface Props {
		config: ConfigCard;
		globalState: GlobalState;
	}

	let { config, globalState }: Props = $props();

	const anyOnline = $derived(config.onlineCount > 0);
	const activeCount = $derived(config.activeInstances.length);
</script>

<Card padding="none" class="flex flex-col overflow-hidden">
	<!-- Card header: status dot + name + optional multi-instance badge -->
	<div class="flex items-start gap-3 border-b border-gray-100 p-4 dark:border-gray-700">
		<!-- Status dot -->
		<div class="mt-1.5 flex-shrink-0 relative flex">
			{#if anyOnline}
				<span class="h-3 w-3 rounded-full absolute animate-ping bg-emerald-400 opacity-75"></span>
				<span class="h-3 w-3 rounded-full bg-emerald-500"></span>
			{:else if activeCount === 0}
				<span class="h-3 w-3 rounded-full bg-gray-200 dark:bg-gray-600"></span>
			{:else}
				<span class="h-3 w-3 rounded-full bg-gray-400 dark:bg-gray-500"></span>
			{/if}
		</div>

		<div class="min-w-0 flex-1">
			<IdentifierLink
				identifier={config.identifier}
				context="config"
				{globalState}
				class="block truncate text-sm font-semibold text-gray-900 dark:text-white"
			/>
			<span
				class="mt-1 inline-block rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500 dark:bg-gray-700 dark:text-gray-400"
			>
				{config.deviceTypeLabel}
			</span>
		</div>

		<!-- Only show N/M badge when there are genuinely multiple active instances -->
		{#if activeCount > 1}
			<span
				class={[
					'flex-shrink-0 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
					anyOnline
						? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200'
						: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
				].join(' ')}
			>
				{config.onlineCount}/{activeCount}
			</span>
		{/if}
	</div>

	<!-- Card body: commit + last seen for active instances -->
	<div class="flex flex-1 flex-col p-4">
		{#if activeCount === 0}
			<p class="text-xs text-gray-400 dark:text-gray-500">{$t('overview.no-instances')}</p>
		{:else}
			<!-- Multiple active instances -->
			<div class="space-y-1">
				{#each config.activeInstances as inst (inst.id)}
					<div class="flex items-center justify-between text-xs">
						<div class="flex items-center gap-1 font-mono text-gray-600 dark:text-gray-300">
							<span
								class={[
									'h-1.5 w-1.5 flex-shrink-0 rounded-full',
									inst.online ? 'bg-emerald-500' : 'bg-gray-400'
								].join(' ')}
							></span>
							<GitCommit class="ml-2 h-3.5 w-3.5 flex-shrink-0" />
							{#if inst.shortCommit}
								<span class="font-mono text-gray-600 dark:text-gray-300">
									{inst.shortCommit}
									{#if inst.isCurrentCommit}
										<HeadTag />
									{/if}
								</span>
							{:else}
								<span class="text-gray-400">{$t('overview.no-commit')}</span>
							{/if}
						</div>
						<span class="text-gray-400 dark:text-gray-500">
							{#if inst.lastSeen}
								<RenderTimeAgo timestamp={inst.lastSeen} />
							{:else}
								{$t('hardware-devices.table.never-seen')}
							{/if}
						</span>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</Card>
