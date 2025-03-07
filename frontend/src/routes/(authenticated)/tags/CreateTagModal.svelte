<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Helper, Input, Label, Modal } from 'flowbite-svelte';
	import { type State, type Tag, saveState } from '$lib/state';
	import { nameToIdentifier, nameValidation } from '$lib/nameValidation';

	interface Props {
		globalState: State;
		open?: boolean;
	}

	let { globalState, open = $bindable(false) }: Props = $props();

	let displayName = $state('');

	const submitData = async () => {
		if (nameValidation(globalState, displayName, 'tag')) return;

		const identifier = nameToIdentifier(displayName);
		const tag: Tag = {
			displayName,
			identifier,
			priority: 90,
			modules: []
		};

		globalState.tags = [...globalState.tags, tag];
		saveState(globalState);
		open = false;
	};
</script>

<Modal
	title={$t('tags.actions.create')}
	{open}
	on:close={() => {
		open = false;
		displayName = '';
	}}
	outsideclose
	bodyClass="p-4 md:p-5 space-y-4 flex-1"
>
	<form class="flex flex-col space-y-4">
		<Label for="display-name">
			{$t('create-configuration.display-name-tag')}
			<Input id="display-name" bind:value={displayName} />
			{#if nameValidation(globalState, displayName, 'tag')}
				<Helper color="red">{nameValidation(globalState, displayName, 'tag')}</Helper>
			{:else}
				<Helper color="green">
					{$t('create-configuration.name-helper-tag', {
						values: { identifier: nameToIdentifier(displayName) }
					})}
				</Helper>
			{/if}
		</Label>
		<div class="flex justify-end">
			<Button
				type="button"
				class="btn btn-primary"
				disabled={!!nameValidation(globalState, displayName, 'tag')}
				on:click={submitData}
			>
				{$t('tags.actions.add')}
			</Button>
		</div>
	</form>
</Modal>
