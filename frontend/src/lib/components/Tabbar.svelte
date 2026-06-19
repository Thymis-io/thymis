<script lang="ts" module>
	import type { Component, ComponentType } from 'svelte';

	export type TabbarItem = {
		name: string;
		href: string;
		icon: Component | ComponentType;
		hidden?: boolean;
	};
</script>

<script lang="ts">
	import { TabItem, Tabs } from 'flowbite-svelte';
	import { page } from '$app/state';

	interface Props {
		items: TabbarItem[];
	}

	let { items }: Props = $props();
</script>

<div class="tabbar-wrap" data-testid="tabbar">
	<Tabs
		contentClass="mb-4"
		defaultClass="flex flex-wrap gap-1 border-b border-[var(--ds-border)] mb-4"
		activeClasses="inline-block text-sm font-medium text-center disabled:cursor-not-allowed p-2 px-3 -mb-px border-b-2 border-[var(--ds-accent)] text-[var(--ds-accent-strong)]"
		inactiveClasses="inline-block text-sm font-medium text-center disabled:cursor-not-allowed p-2 px-3 -mb-px border-b-2 border-transparent text-[var(--ds-text-dim)] hover:text-[var(--ds-text)]"
	>
		{#each items as item}
			{#if !item.hidden}
				<a href={item.href + page.url.search}>
					<TabItem open={page.url.pathname === item.href}>
						<div
							slot="title"
							class="font-semibold flex items-center px-1 gap-2 md:min-w-32 xl:min-w-48"
						>
							<item.icon size={18} />
							<span>{item.name}</span>
						</div>
					</TabItem>
				</a>
			{/if}
		{/each}
	</Tabs>
</div>

<style>
	/* Flowbite Tabs renders its own 1px divider after the tab list; the tab
	   list already has a bottom border, so hide the redundant one. */
	.tabbar-wrap :global(div.h-px) {
		display: none;
	}
</style>
