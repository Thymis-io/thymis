<script lang="ts">
	import { browser } from '$app/environment';
	import EllipsisVertical from 'lucide-svelte/icons/ellipsis-vertical';
	import type { Component, ComponentType } from 'svelte';

	export type RowMenuItem = {
		label: string;
		icon?: Component | ComponentType;
		/** Renders an <a> instead of a <button> when set. */
		href?: string;
		/** Adds the `download` attribute on an `href` item. */
		download?: boolean;
		onclick?: () => void;
		variant?: 'default' | 'danger';
		disabled?: boolean;
	};

	interface Props {
		items: RowMenuItem[];
		/** Accessible label for the trigger button. */
		label?: string;
		menuWidth?: number;
	}

	let { items, label = 'Row actions', menuWidth }: Props = $props();

	let open = $state(false);
	let triggerEl = $state<HTMLButtonElement>();
	let menuStyle = $state('');

	const MENU_WIDTH = $derived(menuWidth || 180);
	const ITEM_HEIGHT = 35;

	const place = () => {
		if (!triggerEl) return;
		const r = triggerEl.getBoundingClientRect();
		const left = Math.max(8, Math.min(r.right - MENU_WIDTH, window.innerWidth - MENU_WIDTH - 8));
		const estHeight = items.length * ITEM_HEIGHT + 8;
		let top = r.bottom + 4;
		if (top + estHeight > window.innerHeight - 8) {
			top = Math.max(8, r.top - estHeight - 4);
		}
		menuStyle = `top: ${top}px; left: ${left}px; min-width: ${MENU_WIDTH}px;`;
	};

	const toggle = (e: MouseEvent) => {
		e.preventDefault();
		e.stopPropagation();
		if (!open) place();
		open = !open;
	};

	const close = () => (open = false);

	const select = (item: RowMenuItem) => {
		if (item.disabled) return;
		close();
		item.onclick?.();
	};

	$effect(() => {
		if (!browser || !open) return;
		const onScroll = () => close();
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') close();
		};
		window.addEventListener('scroll', onScroll, true);
		window.addEventListener('resize', close);
		document.addEventListener('click', close);
		document.addEventListener('keydown', onKey);
		return () => {
			window.removeEventListener('scroll', onScroll, true);
			window.removeEventListener('resize', close);
			document.removeEventListener('click', close);
			document.removeEventListener('keydown', onKey);
		};
	});
</script>

<button
	bind:this={triggerEl}
	type="button"
	class="ds-icon-btn"
	aria-label={label}
	aria-haspopup="menu"
	aria-expanded={open}
	onclick={toggle}
>
	<EllipsisVertical size={16} />
</button>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		class="ds-row-menu"
		style="position: fixed; {menuStyle}"
		role="menu"
		tabindex="-1"
		onclick={(e) => e.stopPropagation()}
	>
		{#each items as item (item.label)}
			{@const Icon = item.icon}
			{#if item.href}
				<a
					class="ds-row-menu-item {item.variant === 'danger' ? 'danger' : ''}"
					href={item.href}
					download={item.download}
					role="menuitem"
					onclick={close}
				>
					{#if Icon}<Icon size={15} />{/if}{item.label}
				</a>
			{:else}
				<button
					type="button"
					class="ds-row-menu-item {item.variant === 'danger' ? 'danger' : ''}"
					role="menuitem"
					disabled={item.disabled}
					onclick={() => select(item)}
				>
					{#if Icon}<Icon size={15} />{/if}{item.label}
				</button>
			{/if}
		{/each}
	</div>
{/if}
