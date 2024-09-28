<script lang="ts">
	import { t } from 'svelte-i18n';
	import Section from './Section.svelte';
	import { type Device } from '$lib/state';

	export let device: Device;

	let className = '';
	export { className as class };
</script>

<Section class={className} title={$t('device-details.network')}>
	<p>{$t('device-details.targetHost')}:</p>
	<p>{device.targetHost}</p>
</Section>
