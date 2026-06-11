<script lang="ts">
	import type { Snippet, ComponentType } from 'svelte';

	interface Props {
		label?: string;
		/** Renders an <a> instead of a <button> when set. */
		href?: string;
		onclick?: (e: MouseEvent) => void;
		variant?: 'default' | 'primary' | 'danger' | 'ghost';
		/** Small (table-row) size by default. */
		size?: 'sm' | 'md';
		icon?: ComponentType;
		disabled?: boolean;
		title?: string;
		'aria-label'?: string;
		class?: string;
		children?: Snippet;
	}

	let {
		label,
		href,
		onclick,
		variant = 'default',
		size = 'sm',
		icon: Icon,
		disabled = false,
		title,
		'aria-label': ariaLabel,
		class: className = '',
		children
	}: Props = $props();

	let cls = $derived(
		[
			'ds-btn',
			size === 'sm' ? 'ds-btn-sm' : '',
			variant === 'primary' ? 'ds-btn-primary' : '',
			variant === 'danger' ? 'ds-btn-danger' : '',
			variant === 'ghost' ? 'ds-btn-ghost' : '',
			className
		]
			.filter(Boolean)
			.join(' ')
	);
</script>

{#if href}
	<a class={cls} {href} {title} aria-label={ariaLabel}>
		{#if Icon}<Icon size={15} />{/if}
		{label}{@render children?.()}
	</a>
{:else}
	<button class={cls} {onclick} {disabled} {title} aria-label={ariaLabel}>
		{#if Icon}<Icon size={15} />{/if}
		{label}{@render children?.()}
	</button>
{/if}
