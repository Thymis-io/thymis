<script lang="ts">
	import { t } from 'svelte-i18n';
	import Page from '$lib/components/layout/Page.svelte';
	import Tabbar from '$lib/components/Tabbar.svelte';
	import Server from 'lucide-svelte/icons/server';
	import HardDrive from 'lucide-svelte/icons/hard-drive';
	import Archive from 'lucide-svelte/icons/archive';

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	let tabs = $derived([
		{ name: $t('hardware-devices.tabs.active'), href: '/devices/active', icon: Server },
		{
			name: $t('hardware-devices.tabs.without-deployment'),
			href: '/devices/without-deployment',
			icon: HardDrive
		},
		{ name: $t('hardware-devices.tabs.archived'), href: '/devices/archived', icon: Archive }
	]);
</script>

<Page title={$t('nav.devices')} subtitle={$t('hardware-devices.subtitle')}>
	<Tabbar items={tabs} />
	{@render children?.()}
</Page>
