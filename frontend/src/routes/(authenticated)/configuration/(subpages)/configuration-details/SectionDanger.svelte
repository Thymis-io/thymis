<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { saveState, type Config, globalState } from '$lib/state';
	import { Button } from 'flowbite-svelte';
	import DeleteConfirm from '$lib/components/DeleteConfirm.svelte';
	import Trash from 'lucide-svelte/icons/trash-2';
	import { goto } from '$app/navigation';

	export let config: Config;

	let configToDelete: Config | undefined = undefined;

	const deleteConfiguration = async (config: Config) => {
		const identifier = config.identifier;
		$globalState.configs = $globalState.configs.filter(
			(config) => config.identifier !== identifier
		);
		await saveState();
		// await goto('/configuration/list');
		setTimeout(async () => await goto('/configuration/list'), 200);
	};

	let className = '';
	export { className as class };
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
