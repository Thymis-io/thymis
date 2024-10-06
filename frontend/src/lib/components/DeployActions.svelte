<script lang="ts">
	import { t } from 'svelte-i18n';
	import { Button } from 'flowbite-svelte';
	import GearsSolid from 'svelte-awesome-icons/GearsSolid.svelte';
	import ArrowsRotateSolid from 'svelte-awesome-icons/ArrowsRotateSolid.svelte';
	import PlaySolid from 'svelte-awesome-icons/PlaySolid.svelte';
	import DeployModal from '$lib/components/DeployModal.svelte';
	import { invalidate } from '$app/navigation';

	const build = async () => {
		await fetch(`/api/action/build`, { method: 'POST' });
	};

	const update = async () => {
		await fetch(`/api/action/update`, { method: 'POST' });
		invalidate((url) => url.pathname === '/api/available_modules');
	};

	let openDeploy = false;
</script>

<div class="flex flex-wrap justify-end align-start gap-1 sm:gap-2 w-96 sm:w-[400px]">
	<Button color="alternative" class="gap-2 px-2 sm:px-4 py-1 sm:py-2 h-min" on:click={build}>
		<PlaySolid class="w-[10px] sm:w-[12px]" />
		<span class="text-xs sm:text-sm">{$t('deploy.build')}</span>
	</Button>
	<Button color="alternative" class="gap-2 px-2 sm:px-4 py-1 sm:py-2 h-min" on:click={update}>
		<ArrowsRotateSolid class="w-[12px] sm:w-[16px]" />
		<span class="text-xs sm:text-sm">{$t('deploy.update')}</span>
	</Button>
	<Button
		color="alternative"
		class="gap-2 px-2 sm:px-4 py-1 sm:py-2 h-min"
		on:click={() => (openDeploy = true)}
	>
		<GearsSolid class="w-[14px] sm:w-[18px]" />
		<span class="text-xs sm:text-sm">{$t('deploy.deploy')}</span>
	</Button>
	<DeployModal bind:open={openDeploy} />
</div>
