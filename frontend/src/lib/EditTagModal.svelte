<script lang="ts">
	import { t } from 'svelte-i18n';
	import { type Config, saveState, state, type Tag } from '$lib/state';
	import { Button, Modal, Label, P } from 'flowbite-svelte';
	import MultiSelect from 'svelte-multiselect';

	export let currentlyEditingConfig: Config | undefined;

	$: projectTags = $state.tags;
	$: tagsSelect = projectTags?.map((tag) => ({ value: tag.identifier, label: tag.displayName }));

	let selectedTags: { value: string; label: string }[] = [];

	const setSelectedTags = (configTags: string[], projectTags: Tag[]) => {
		selectedTags = configTags?.map((tag) => ({
			value: tag,
			label: projectTags.find((t) => t.identifier === tag)?.displayName ?? ''
		}));
	};

	$: setSelectedTags(currentlyEditingConfig?.tags || [], projectTags);
</script>

<Modal
	title={$t('configurations.edit-tags-title')}
	open={!!currentlyEditingConfig}
	on:close={() => (currentlyEditingConfig = undefined)}
	outsideclose
	bodyClass="p-4 md:p-5 space-y-4 flex-1"
>
	<div class="w-full">
		{#if projectTags.length > 0}
			<Label for="tags">
				{$t('create-configuration.tags')}
				<MultiSelect
					id="tags"
					options={tagsSelect}
					bind:selected={selectedTags}
					outerDivClass="w-full"
				/>
			</Label>
		{:else}
			<P>{$t('create-configuration.no-tags')}</P>
		{/if}
	</div>
	<div class="flex justify-end gap-2">
		<Button
			on:click={async () => {
				if (currentlyEditingConfig) {
					currentlyEditingConfig.tags = selectedTags.map((tag) => tag.value);
				}
				await saveState();
				currentlyEditingConfig = undefined;
			}}
		>
			{$t('common.save')}
		</Button>
	</div>
</Modal>
