<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button } from 'flowbite-svelte';
	import { GearsSolid, ArrowsRotateSolid, PlaySolid } from 'svelte-awesome-icons';
	import '../app.postcss';
	import { controllerHost, controllerProtocol } from './api';
	import DeployModal from '$lib/DeployModal.svelte';

	const build = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetch(`${controllerProtocol}://${controllerHost}/action/update`, { method: 'POST' });
	};

	let openDeploy = false;
</script>

<div class="gap-2">
	<Button color="alternative" class="min-w-32 gap-2" on:click={build}>
		<PlaySolid size="18" />
		<span class="my-0.5">{$t('deploy.build')}</span>
	</Button>
	<Button color="alternative" class="min-w-32 gap-2" on:click={() => (openDeploy = true)}>
		<GearsSolid size="18" />
		<span class="my-0.5">{$t('deploy.deploy')}</span>
	</Button>
	<Button color="alternative" class="min-w-32 gap-2" on:click={update}>
		<ArrowsRotateSolid size="16" />
		<span class="my-0.5">{$t('deploy.update')}</span>
	</Button>
	<DeployModal bind:open={openDeploy} />
</div>
