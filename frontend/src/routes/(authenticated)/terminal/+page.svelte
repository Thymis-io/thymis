<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import { globalNavSelectedDevice } from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">{$t('nav.terminal')}</h1>
	<DeployActions />
</div>
<Terminal device={$globalNavSelectedDevice} />
