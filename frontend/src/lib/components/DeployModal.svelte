<script lang="ts">
	import { t } from 'svelte-i18n';
	import { controllerHost, controllerProtocol } from '../api';
	import { Button, Modal, Label, Input } from 'flowbite-svelte';
	import { invalidate } from '$app/navigation';

	export let open = false;

	$: summary = new Date().toLocaleString() + ': ';

	const deploy = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/deploy?summary=${summary}`, {
			method: 'POST'
		});
		await invalidate((url) => url.pathname === '/api/history');

		open = false;
	};
</script>

<Modal bind:open title={$t('deploy.deploy')} autoclose outsideclose>
	<div>
		<Label class="block mb-2">{$t('deploy.summary')}</Label>
		<Input type="text" bind:value={summary} placeholder={$t('deploy.summary')} />
	</div>
	<div class="flex flex-wrap gap-2 justify-end">
		<Button on:click={deploy}>{$t('deploy.deploy')}</Button>
	</div>
</Modal>
