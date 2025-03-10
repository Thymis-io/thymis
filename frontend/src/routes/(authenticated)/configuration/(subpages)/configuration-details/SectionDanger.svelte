<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { saveState, type Config } from '$lib/state';
	import { Button } from 'flowbite-svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import Trash from 'lucide-svelte/icons/trash-2';
	import { goto } from '$app/navigation';
	import type { GlobalState } from '$lib/state.svelte';

	interface Props {
		globalState: GlobalState;
		config: Config;
		class?: string;
	}

	let { globalState, config, class: className = '' }: Props = $props();

	let configToDelete: Config | undefined = $state(undefined);

	const deleteConfiguration = async (config: Config) => {
		const identifier = config.identifier;
		globalState.configs = globalState.configs.filter((config) => config.identifier !== identifier);
		await saveState(globalState);
		// await goto('/configuration/list');
		setTimeout(async () => await goto('/configuration/list'), 200);
	};
</script>

<DeleteConfirm
	target={configToDelete?.displayName}
	on:confirm={() => {
		if (configToDelete) deleteConfiguration(configToDelete);
		configToDelete = undefined;
	}}
	on:cancel={() => (configToDelete = undefined)}
/>
<Section class={className} title={$t('configuration-details.danger')}>
	<Button
		class="px-2 py-1.5 gap-2 justify-start"
		color="alternative"
		on:click={() => (configToDelete = config)}
	>
		<Trash size="16" />
		{$t('configurations.actions.delete')}
	</Button>
</Section>
