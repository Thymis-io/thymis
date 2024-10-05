<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button, Helper, Input, Label, Modal } from 'flowbite-svelte';
	import { type Tag, state, saveState } from '$lib/state';
	import { nameToIdentifier, nameValidation } from '$lib/nameValidation';

	export let open = false;

	let displayName = '';

	const submitData = async () => {
		if (nameValidation(displayName, 'tag')) return;

		const identifier = nameToIdentifier(displayName);
		const tag: Tag = {
			displayName,
			identifier,
			priority: 90,
			modules: []
		};

		$state.tags = [...$state.tags, tag];
		saveState();
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
		<Label for="displayName">
			{$t('create-device.display-name-tag')}
			<Input id="displayName" bind:value={displayName} />
			{#if nameValidation(displayName, 'tag')}
				<Helper color="red">{nameValidation(displayName, 'tag')}</Helper>
			{:else}
				<Helper color="green">
					{$t('create-device.name-helper-tag', {
						values: { identifier: nameToIdentifier(displayName) }
					})}
				</Helper>
			{/if}
		</Label>
		<div class="flex justify-end">
			<Button
				type="button"
				class="btn btn-primary"
				disabled={!!nameValidation(displayName, 'tag')}
				on:click={submitData}
			>
				{$t('tags.actions.add')}
			</Button>
		</div>
	</form>
</Modal>
