<script lang="ts">
	import { t } from 'svelte-i18n';
	import IdentifierLink from '#lib/IdentifierLink.svelte';
	import type { GlobalState } from '#lib/state.svelte.js';

	interface Props {
		deploymentInfoId: string;
		reason: string;
		globalState: GlobalState;
	}

	let { deploymentInfoId, reason, globalState }: Props = $props();

	// keep `{device}` literal so the link can be rendered in its place
	let [before, after] = $derived(
		$t('notifications.reboot-recommended', { values: { reason, device: '{device}' } }).split(
			'{device}'
		)
	);
</script>

<span>
	{before}
	<IdentifierLink
		identifier={deploymentInfoId}
		context="device"
		{globalState}
		class="inline-block align-middle font-medium"
	/>
	{after}
</span>
