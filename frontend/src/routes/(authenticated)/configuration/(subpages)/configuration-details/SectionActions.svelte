<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Config } from '$lib/state';
	import { Button, Input, Tooltip } from 'flowbite-svelte';
	import Download from 'lucide-svelte/icons/download';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import Play from 'lucide-svelte/icons/play';
	import { fetchWithNotify } from '$lib/fetchWithNotify';
	import { getConfigImageFormat } from '$lib/config/configUtils';

	const restartDevices = async (config: Config) => {
		await fetchWithNotify(`/api/action/restart-device?identifier=${config.identifier}`, {
			method: 'POST'
		});
	};

	interface Props {
		config: Config;
		class?: string;
	}

	let { config, class: className = '' }: Props = $props();
</script>

<Section class={className} title={$t('configuration-details.actions')}>
	<Button
		class="px-2 py-1.5 gap-2 justify-start"
		color="alternative"
		on:click={() => restartDevices(config)}
	>
		<RotateCcw size={'1rem'} class="min-w-4" />
		{$t('configurations.actions.restart')}
	</Button>
</Section>
