<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Config } from '$lib/state';
	import RotateCcw from 'lucide-svelte/icons/rotate-ccw';
	import { fetchWithNotify } from '$lib/fetchWithNotify';

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
	<button class="ds-btn justify-start self-start" onclick={() => restartDevices(config)}>
		<RotateCcw size={'1rem'} class="min-w-4" />
		{$t('configurations.actions.restart')}
	</button>
</Section>
