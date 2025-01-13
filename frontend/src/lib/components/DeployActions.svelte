<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button } from 'flowbite-svelte';
	import Hammer from 'lucide-svelte/icons/hammer';
	import Refresh from 'lucide-svelte/icons/refresh-ccw';
	import Boxes from 'lucide-svelte/icons/boxes';
	import Wallet from 'lucide-svelte/icons/wallet';
	import DeployModal from '$lib/components/DeployModal.svelte';
	import { invalidate } from '$app/navigation';
	import { fetchWithNotify } from '$lib/fetchWithNotify';

	const build = async () => {
		await fetchWithNotify(`/api/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetchWithNotify(`/api/action/update`, { method: 'POST' });
		invalidate((url) => url.pathname === '/api/available_modules');
	};

	let openDeploy = false;
</script>

<div class="flex flex-wrap justify-end align-start my-1.5 gap-1 sm:gap-2 w-96 sm:w-[400px]">
	<Button color="alternative" class="gap-2 px-2 py-1.5 h-min" on:click={build}>
		<Hammer size={'1rem'} class="min-w-4" />
		<span class="text-base">{$t('deploy.build')}</span>
	</Button>
	<Button color="alternative" class="gap-2 px-2 py-1.5 h-min" on:click={update}>
		<Refresh size={'1rem'} class="min-w-4" />
		<span class="text-base">{$t('deploy.update')}</span>
	</Button>
	<Button color="alternative" class="gap-2 px-2 py-1.5 h-min" on:click={() => (openDeploy = true)}>
		<Boxes size={'1rem'} class="min-w-4" />
		<span class="text-base">{$t('deploy.deploy')}</span>
	</Button>
	<DeployModal bind:open={openDeploy} />
</div>
