<script lang="ts">
	import { page } from '$app/stores';
	import { TabItem, Tabs } from 'flowbite-svelte';
	import { t } from 'svelte-i18n';

	import SlidersSolid from 'svelte-awesome-icons/SlidersSolid.svelte';
	import TerminalSolid from 'svelte-awesome-icons/TerminalSolid.svelte';
	import ScreenShare from 'lucide-svelte/icons/screen-share';
	import ListCollapse from 'lucide-svelte/icons/list-collapse';
	import {
		globalNavSelectedConfig,
		globalNavSelectedTag,
		globalNavSelectedTarget,
		state
	} from '$lib/state';
	import { targetShouldShowVNC } from '$lib/vnc/vnc';

	type NavItem = {
		name: string;
		icon: any;
		href: string;
		hidden?: boolean;
		children?: Record<string, string>;
	};

	$: selectedTargetHasAnyVNCModule =
		$globalNavSelectedTarget && targetShouldShowVNC($globalNavSelectedTarget, $state);

	let dynamicNavItems: NavItem[] = [];
	$: dynamicNavItems = [
		{
			name: $t(`nav.device-details`),
			icon: ListCollapse,
			href: '/configuration/configuration-details',
			hidden: !$globalNavSelectedConfig
		},
		{
			name: $t(`nav.config-device`),
			icon: SlidersSolid,
			href: '/configuration/edit',
			hidden: !$globalNavSelectedConfig
		},
		{
			name: $t(`nav.config-tag`),
			icon: SlidersSolid,
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
			icon: TerminalSolid,
			href: '/configuration/terminal',
			hidden: !$globalNavSelectedConfig
		}
	];
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
					<div
						slot="title"
						class="font-semibold flex items-center px-1 gap-2 md:min-w-32 xl:min-w-48"
					>
						<svelte:component this={item.icon} size={18} />
						<span>{item.name}</span>
					</div>
				</TabItem>
			</a>
		{/if}
	{/each}
</Tabs>
