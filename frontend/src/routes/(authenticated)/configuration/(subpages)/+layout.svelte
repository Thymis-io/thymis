<script lang="ts">
	import { t } from 'svelte-i18n';
	import { globalNavSelectedTargetType, globalNavSelectedTarget } from '$lib/state';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import Tabbar from '$lib/components/Tabbar.svelte';
</script>

<div class="flex justify-between mb-4">
	<h1 class="text-3xl font-bold dark:text-white">
		{#if $globalNavSelectedTargetType === 'config'}
			{$t('configurations.details-title')}: {$globalNavSelectedTarget?.displayName ?? ''}
		{:else if $globalNavSelectedTargetType === 'tag'}
			{$t('tags.details-title')}: {$globalNavSelectedTarget?.displayName ?? ''}
		{:else}
			{$globalNavSelectedTarget?.displayName ?? ''}
		{/if}
	</h1>
	<DeployActions />
</div>
<Tabbar />
<slot />
