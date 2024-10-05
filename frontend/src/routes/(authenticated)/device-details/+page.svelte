<script lang="ts">
	import { t } from 'svelte-i18n';
	import type { PageData } from './$types';
	import { Badge, Card } from 'flowbite-svelte';
	import {
		globalNavSelectedDevice,
		globalNavSelectedTag,
		globalNavSelectedTargetType,
		state
	} from '$lib/state';
	import Circle from 'lucide-svelte/icons/circle';
	import DeployActions from '$lib/components/DeployActions.svelte';
	import SectionConfiguration from './SectionConfiguration.svelte';
	import SectionActions from './SectionActions.svelte';
	import SectionDanger from './SectionDanger.svelte';
	import SectionHostkey from './SectionHostkey.svelte';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';
	import VncView from '$lib/vnc/VncView.svelte';
	import Section from './Section.svelte';
	import Terminal from '$lib/terminal/Terminal.svelte';

	export let data: PageData;

	$: currentDevice = $globalNavSelectedDevice;
</script>

{#if $globalNavSelectedTargetType === 'device' && currentDevice}
	<div class="flex justify-between mb-4">
		<div class="flex flex-wrap gap-4 items-center">
			<h1 class="text-3xl font-bold dark:text-white">{currentDevice.displayName}</h1>
			<!-- <Badge large class="p-2 py-0.5 gap-1 self-center">
				<Circle size={15} color="lightgreen" />
				<span class="text-nowrap"> Online </span>
			</Badge> -->
		</div>
		<DeployActions />
	</div>
	<div class="grid grid-cols-4 grid-flow-row gap-x-4 gap-y-12 mt-8">
		<SectionHostkey class="col-span-3" hostkey={data.hostkey} device={currentDevice} />
		<SectionActions class="col-span-1" device={currentDevice} />
		<SectionConfiguration
			class="col-span-3"
			device={currentDevice}
			availableModules={data.availableModules}
		/>
		<SectionDanger class="col-span-1" device={currentDevice} />
		{#if targetShouldShowVNC(currentDevice, $state)}
			<Section class="col-span-2" title={$t('nav.device-vnc')}>
				<VncView device={currentDevice} />
			</Section>
		{/if}
		<Section class="col-span-2" title={$t('nav.terminal')}>
			<Card class="w-full max-w-none" padding="sm">
				<Terminal device={currentDevice} />
			</Card>
		</Section>
	</div>
{:else if $globalNavSelectedTargetType === 'tag' && $globalNavSelectedTag}
	<div class="grid grid-cols-3 gap-4">
		{#each data.state.devices.filter( (device) => device.tags.includes($globalNavSelectedTag.identifier) ) as device}
			<p>Test</p>
		{/each}
	</div>
{/if}
