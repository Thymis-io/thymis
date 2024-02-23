<script lang="ts">
	import { getModalStore, popup, type PopupSettings } from '@skeletonlabs/skeleton';
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

<button class="btn variant-filled" on:click={build}>
	<span><Play /></span><span>Build</span>
</button>
<button class="btn variant-filled" on:click={openDeploy}>
	<span><CloudCog /></span><span>Deploy</span>
</button>
<button class="btn variant-filled" on:click={update}>
	<span><CloudCog /></span><span>Update</span>
</button>
