<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { Module } from '$lib/state';
	import { Card, P } from 'flowbite-svelte';

	export let module: Module;
</script>

<Card class="max-w-none grid grid-cols-4 gap-8">
	{#each Object.entries(module.settings) as [key, value]}
		<P class="col-span-1">
			{$t(`options.nix.${value.name}`, { default: value.name })}
		</P>
		<div class="col-span-1" />
		<P class="col-span-2">{value.description}</P>
	{:else}
		<div class="col-span-1">{$t('options.no-settings')}</div>
	{/each}
</Card>
