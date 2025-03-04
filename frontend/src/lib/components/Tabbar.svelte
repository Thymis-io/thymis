<script lang="ts">
	import { run } from 'svelte/legacy';

	import { page } from '$app/stores';
	import { TabItem, Tabs } from 'flowbite-svelte';
	import { t } from 'svelte-i18n';

	import Sliders from 'lucide-svelte/icons/sliders-horizontal';
	import Terminal from 'lucide-svelte/icons/terminal';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import ListCollapse from 'lucide-svelte/icons/list-collapse';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTarget,
		globalState
	} from '$lib/state';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

	type NavItem = {
		name: string;
		icon: any;
		href: string;
		hidden?: boolean;
		children?: Record<string, string>;
	};

	let selectedTargetHasAnyVNCModule = $derived(
		$globalNavSelectedTarget && targetShouldShowVNC($globalNavSelectedTarget, $globalState)
	);

	let dynamicNavItems: NavItem[] = $state([]);
	run(() => {
		dynamicNavItems = [
			{
				name: $t(`nav.device-details`),
				icon: ListCollapse,
				href: '/configuration/configuration-details',
				hidden: !$globalNavSelectedConfig
			},
			{
				name: $t(`nav.configure`),
				icon: Sliders,
				href: '/configuration/edit',
				hidden: !$globalNavSelectedConfig
			},
			{
				name: $t(`nav.config-tag`),
				icon: Sliders,
				href: '/configuration/edit',
				hidden: !$globalNavSelectedTag
			},
			{
				name: $t('nav.device-vnc'),
				icon: ScreenShare,
				href: '/configuration/vnc',
				hidden: !selectedTargetHasAnyVNCModule
			},
			{
				name: $t('nav.terminal'),
				icon: Terminal,
				href: '/configuration/terminal',
				hidden: !$globalNavSelectedConfig
			}
		];
	});
</script>

<Tabs
	contentClass="mb-4"
	defaultClass="flex flex-wrap gap-x-2"
	activeClasses="inline-block text-sm font-medium text-center rounded-t-lg disabled:cursor-not-allowed p-2 bg-gray-100 dark:bg-gray-800 text-primary-600 dark:text-primary-400"
	inactiveClasses="inline-block text-sm font-medium text-center rounded-t-lg disabled:cursor-not-allowed p-2 hover:bg-gray-100 dark:hover:bg-gray-800"
>
	{#each dynamicNavItems as item}
		{#if !item.hidden}
			<a href={item.href + $page.url.search}>
				<TabItem open={$page.url.pathname === item.href}>
					{#snippet title()}
						<div class="font-semibold flex items-center px-1 gap-2 md:min-w-32 xl:min-w-48">
							<item.icon size={18} />
							<span>{item.name}</span>
						</div>
					{/snippet}
				</TabItem>
			</a>
		{/if}
	{/each}
</Tabs>
