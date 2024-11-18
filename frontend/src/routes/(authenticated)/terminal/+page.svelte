<script lang="ts">
	import { t } from 'svelte-i18n';
	import Terminal from '$lib/terminal/Terminal.svelte';
	import { globalNavSelectedDevice, globalNavSelectedTarget } from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import Tabbar from '$lib/components/Tabbar.svelte';
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">{$globalNavSelectedTarget?.displayName}</h1>
	<DeployActions />
</div>
<Tabbar />
<Terminal device={$globalNavSelectedDevice} />
