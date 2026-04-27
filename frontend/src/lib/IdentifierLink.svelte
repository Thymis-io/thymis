<script lang="ts">
	import { t } from 'svelte-i18n';
	import { page } from '$app/state';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import type { ContextType } from './state';
	import type { GlobalState } from './state.svelte';
	import { buildGlobalNavSearchParam } from './searchParamHelpers';
	import type { DeploymentInfo } from './deploymentInfo';

	interface Props {
		globalState: GlobalState;
		deploymentInfos?: DeploymentInfo[];
		identifier?: string | null;
		context?: ContextType | 'device' | null;
		showLinkHover?: boolean;
		solidBackground?: boolean;
		iconSize?: number | string;
		class?: string;
	}

	let {
		identifier,
		deploymentInfos,
		context,
		globalState,
		showLinkHover = true,
		solidBackground = false,
		iconSize = '1rem',
		class: className
	}: Props = $props();

	let target = $derived.by(() => {
		if (!context || !identifier) return null;
		if (context === 'tag') {
			return globalState.tag(identifier);
		} else if (context === 'config') {
			return globalState.config(identifier);
		} else if (context === 'device') {
			return null;
		} else {
			const _: never = context;
		}
	});

	let deviceDeploymentInfo = $derived.by(() => {
		if (context !== 'device' || !identifier || !deploymentInfos) return null;
		return deploymentInfos.find((d) => d.id === identifier) ?? null;
	});
</script>

{#if target}
	<div class={'relative hover-parent ' + className}>
		{#if context === 'tag'}
			<a
				href={`/configuration/edit?${buildGlobalNavSearchParam(globalState, page.url.search, context, identifier)}`}
				class={'min-h-6 flex items-center gap-1 w-fit ' +
					(showLinkHover ? 'hover:underline ' : '') +
					(solidBackground
						? 'p-1 px-2 bg-primary-700 hover:bg-primary-800 dark:bg-primary-600 dark:hover:bg-primary-700 rounded text-white '
						: '')}
			>
				<TagIcon size={iconSize} />
				{target.displayName}
			</a>
		{:else if context === 'config'}
			<a
				href={`/configuration/configuration-details?${buildGlobalNavSearchParam(globalState, page.url.search, context, identifier)}`}
				class={'min-h-6 flex items-center gap-1 w-fit ' +
					(showLinkHover ? 'hover:underline ' : '') +
					(solidBackground
						? 'p-1 2px-2 bg-primary-700 hover:bg-primary-800 dark:bg-primary-600 dark:hover:bg-primary-700 rounded text-white '
						: '')}
			>
				<FileCode size={iconSize} />
				{target.displayName}
			</a>
		{/if}
		<!--
        <div class="hover-child text-base">
			<div class="relative bg-gray-600 p-1 rounded bottom-2">{$t('nav.hardware-devices')}:</div>
		</div>
        -->
	</div>
{/if}

{#if context == 'device'}
	<a
		href={`/devices/${identifier}`}
		class={'min-h-6 flex items-center gap-1 w-fit ' +
			(showLinkHover ? 'hover:underline ' : '') +
			(solidBackground
				? 'p-1 px-2 bg-primary-700 hover:bg-primary-800 dark:bg-primary-600 dark:hover:bg-primary-700 rounded text-white '
				: '')}
	>
		<HardDrive size={iconSize} class="shrink-0" />
		{deviceDeploymentInfo?.name ?? deviceDeploymentInfo?.id ?? identifier}
	</a>
{/if}

<style>
	.hover-child {
		position: absolute;
		left: 0;
		bottom: 1.5rem;
	}

	.hover-parent .hover-child {
		display: none;
	}

	.hover-parent:hover .hover-child {
		display: block;
	}
</style>
