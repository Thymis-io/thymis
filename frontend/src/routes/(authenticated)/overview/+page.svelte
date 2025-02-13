<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Card, P } from 'flowbite-svelte';
	import { state } from '$lib/state';
	import PageHead from '$lib/components/PageHead.svelte';

	export let data: PageData;
</script>

<PageHead title={$t('nav.overview')} />
<!-- container for a bunch of cards -->
<div class="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4">
	<Card class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-primary-500 rounded-full p-5 w-full">
				<P weight="bold" size="2xl" color="text-white dark:text-gray-900">
					{$t('overview.configs', { values: { count: $state.configs.length } })}
				</P>
			</div>
		</div>
	</Card>

	<Card class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-primary-500 rounded-full p-5 w-full">
				<P weight="bold" size="2xl" color="text-white dark:text-gray-900">
					{$t('overview.tags', { values: { count: $state.tags.length } })}
				</P>
			</div>
		</div>
	</Card>

	<Card class="card p-4 bg-white rounded-lg shadow-md w-full">
		<div class="flex items-center justify-around">
			<div class="flex items-center justify-center bg-primary-500 rounded-full p-5 w-full">
				<P weight="bold" size="2xl" color="text-white dark:text-gray-900">
					{$t('overview.modules', { values: { count: data.availableModules.length } })}
				</P>
			</div>
		</div>
	</Card>
</div>
