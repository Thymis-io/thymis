<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Card } from 'flowbite-svelte';
	import ModuleList from '$lib/config/ModuleList.svelte';
	import { getTagByIdentifier } from '$lib/state';
	import type { ModuleSettingsWithOrigin, Tag, Config, Module, Origin } from '$lib/state';
	import type { PageData } from './$types';
	import ModuleCard from '$lib/config/ModuleCard.svelte';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import TagIcon from 'lucide-svelte/icons/tag';

	interface Props {
		data: PageData;
		children?: import('svelte').Snippet;
	}

	let { data, children }: Props = $props();

	const getOrigin = (target: Tag | Config): Origin => {
		return {
			originId: target.identifier,
			originContext: 'tags' in target ? 'config' : 'tag',
			originName: target.displayName
		};
	};

	const getModuleSettings = (target: Tag | Config | undefined): ModuleSettingsWithOrigin[] => {
		if (!target) {
			return [];
		}

		let ownModules: ModuleSettingsWithOrigin[] = getOwnModuleSettings(target);
		let tagModules: ModuleSettingsWithOrigin[] = [];

		if ('tags' in target) {
			let usedTags = target.tags.flatMap((t) => getTagByIdentifier(data.globalState, t) ?? []);

			tagModules = usedTags.flatMap((t) =>
				t.modules.map((m) => ({ ...getOrigin(t), priority: t.priority, ...m }))
			);
		}

		return [...ownModules, ...tagModules];
	};

	const getOwnModuleSettings = (target: Tag | Config | undefined): ModuleSettingsWithOrigin[] => {
		return target?.modules.map((m) => ({ ...getOrigin(target), priority: undefined, ...m })) ?? [];
	};

	const getSelfModules = (selectedTarget: Tag | Config | undefined) => {
		let settings = getOwnModuleSettings(selectedTarget);
		return data.availableModules.filter((m) => settings.find((s) => s.type === m.type)) ?? [];
	};

	const getOtherSettings = (target: Config | Tag | undefined, module: Module | undefined) => {
		return getModuleSettings(target)?.filter((s) => s.type === module?.type);
	};
</script>

<div class="grid grid-flow-row grid-cols-1 md:grid-cols-[250px_auto] gap-4">
	<Card class="max-w-none" padding={'sm'}>
		<ModuleList
			nav={data.nav}
			globalState={data.globalState}
			contextType={data.nav.selectedTargetType}
			context={data.globalState.selectedTarget}
			selfModules={getSelfModules(data.nav.selectedTarget)}
			availableModules={data.availableModules}
		>
			{#snippet icon()}
				{#if children}{@render children()}{:else if data.nav.selectedTag}
					<TagIcon size="20" />
				{:else if data.nav.selectedConfig}
					<FileCode size="20" />
				{/if}
			{/snippet}
		</ModuleList>
		{#each data.nav.selectedConfig?.tags ?? [] as tagIdentifier}
			<div class="mt-6">
				<ModuleList
					nav={data.nav}
					globalState={data.globalState}
					contextType="tag"
					context={data.globalState.tag(tagIdentifier)}
					selfModules={getSelfModules(data.globalState.tag(tagIdentifier))}
				>
					{#snippet icon()}
						<TagIcon size="20" />
					{/snippet}
				</ModuleList>
			</div>
		{/each}
	</Card>
	{#if data.nav.selectedModule && data.nav.selectedModuleContextType && data.nav.selectedModuleContext?.modules.find((m) => m.type === data.nav.selectedModule?.type)}
		<ModuleCard
			nav={data.nav}
			globalState={data.globalState}
			module={data.nav.selectedModule}
			settings={getOwnModuleSettings(data.nav.selectedModuleContext).find(
				(s) => s.type === data.nav.selectedModule?.type
			)}
			otherSettings={getOtherSettings(data.nav.selectedTarget, data.nav.selectedModule)}
			showRouting={data.nav.selectedTargetType === 'config'}
			canEdit={data.nav.selectedTarget === data.nav.selectedModuleContext}
		/>
	{/if}
</div>
