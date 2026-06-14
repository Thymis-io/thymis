<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from '$lib/components/layout/Section.svelte';
	import { type Config, type Module } from '$lib/state';
	import { buildConfigSelectModuleSearchParam } from '$lib/searchParamHelpers';
	import { page } from '$app/stores';
	import Pen from 'lucide-svelte/icons/pen';
	import EditTagModal from '$lib/EditTagModal.svelte';
	import ModuleIcon from '$lib/config/ModuleIcon.svelte';
	import type { GlobalState } from '$lib/state.svelte';
	import IdentifierLink from '$lib/IdentifierLink.svelte';

	interface Props {
		globalState: GlobalState;
		config: Config;
		availableModules: Module[];
		class?: string;
	}

	let { globalState, config, availableModules, class: className = '' }: Props = $props();

	let currentlyEditingConfig: Config | undefined = $state(undefined);

	const getOwnModules = (config: Config, availableModules: Module[]) => {
		return config.modules
			.map((module) => availableModules.find((m) => m.type === module.type))
			.filter((m) => !!m);
	};

	const findTag = (identifier: string) => {
		return globalState.tags.find((t) => t.identifier === identifier);
	};
</script>

<EditTagModal {globalState} bind:currentlyEditingConfig />
<Section class={className} title={$t('configuration-details.config')}>
	{@const ownModules = getOwnModules(config, availableModules)}
	<p class="cfg-label">{$t('configuration-details.modules')}</p>
	<div class="flex flex-wrap items-center gap-2 text-base">
		{#each ownModules as module}
			<a
				href={`/configuration/edit?${buildConfigSelectModuleSearchParam(
					globalState,
					$page.url.search,
					'config',
					config.identifier,
					'config',
					config.identifier,
					module
				)}`}
				class="cfg-module"
			>
				<ModuleIcon {module} theme="dark" />
				<span class="text-nowrap">{module.displayName}</span>
				<Pen size="14" class="opacity-80" />
			</a>
		{:else}
			<span class="cfg-empty">{$t('configuration-details.no-modules')}</span>
		{/each}
	</div>

	<p class="cfg-label mt-4">{$t('configuration-details.tags')}</p>
	<div class="flex flex-wrap items-center gap-3 text-base">
		<div class="flex flex-wrap gap-2">
			{#each config.tags as tag (tag)}
				<IdentifierLink identifier={tag} context="tag" {globalState} solidBackground />
			{:else}
				<span class="cfg-empty">{$t('configuration-details.no-tags')}</span>
			{/each}
		</div>
		<button class="ds-btn ds-btn-sm" onclick={() => (currentlyEditingConfig = config)}>
			<Pen size="16" />
			<span>{$t('configuration-details.edit-tags')}</span>
		</button>
	</div>
</Section>

<style lang="postcss">
	.cfg-label {
		font-size: 11.5px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--ds-text-mute);
		margin-bottom: 8px;
	}
	.cfg-module {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 5px 10px;
		border-radius: 7px;
		background: var(--ds-accent);
		color: #fff;
		font-size: 13.5px;
		font-weight: 500;
		transition: background 0.12s;
	}
	.cfg-module:hover {
		background: var(--ds-accent-strong);
	}
	.cfg-empty {
		font-size: 13px;
		color: var(--ds-text-mute);
	}
</style>
