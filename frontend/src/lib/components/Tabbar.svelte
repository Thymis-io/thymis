<script lang="ts" module>
	import type { Component, ComponentType } from 'svelte';

	export type TabbarItem = {
		name: string;
		href: string;
		icon: Component | ComponentType;
		hidden?: boolean;
		count?: number;
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
				{@const active = page.url.pathname === item.href}
				<a href={item.href + page.url.search}>
					<TabItem open={active}>
						<div slot="title" class="font-semibold flex items-center px-1 gap-2">
							<item.icon size={18} />
							<span>{item.name}</span>
							{#if item.count !== undefined}
								<span class="tab-badge {active ? 'active' : ''}">{item.count}</span>
							{/if}
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

	/* Count badge — mirrors the sidebar nav badge so counts read consistently
	   across the app; tints to the accent colour on the active tab. */
	.tab-badge {
		font-size: 11px;
		padding: 1px 6px;
		border-radius: 999px;
		background: var(--ds-surface-3);
		color: var(--ds-text-dim);
	}
	.tab-badge.active {
		background: var(--ds-accent-dim);
		color: var(--ds-accent-strong);
	}
</style>
