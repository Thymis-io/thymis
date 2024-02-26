<script lang="ts">
	import { getModalStore, popup, type PopupSettings } from '@skeletonlabs/skeleton';
	import { Button } from 'flowbite-svelte';
	import CloudCog from 'lucide-svelte/icons/cloud-cog';
	import Play from 'lucide-svelte/icons/play';
	import '../app.postcss';
	import { controllerHost, controllerProtocol } from './api';

	let modalStore = getModalStore();

	const build = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/update`, { method: 'POST' });
	};

	const openDeploy = () => {
		modalStore.trigger({
			type: 'component',
			component: 'DeployModal',
			title: 'Deploy'
		});
	};
</script>

<Button color="alternative" on:click={build}>
	<span><Play /></span><span>Build</span>
</Button>
<Button color="alternative" on:click={openDeploy}>
	<span><CloudCog /></span><span>Deploy</span>
</Button>
<Button color="alternative" on:click={update}>
	<span><CloudCog /></span><span>Update</span>
</Button>
