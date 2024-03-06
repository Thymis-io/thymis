<script lang="ts">
	import { controllerHost, controllerProtocol } from './api';
	import { Button, Modal, Label, Input } from 'flowbite-svelte';

	export let open = false;

	$: summary = new Date().toLocaleString() + ': ';

	const deploy = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/deploy?summary=${summary}`, {
			method: 'POST'
		});

		open = false;
	};
</script>

<Modal bind:open title="Deploy" autoclose outsideclose>
	<div>
		<Label class="block mb-2">Summary</Label>
		<Input type="text" bind:value={summary} placeholder="Summary" />
	</div>
	<div class="flex flex-wrap gap-2 justify-end">
		<Button on:click={deploy}>Deploy</Button>
	</div>
</Modal>
