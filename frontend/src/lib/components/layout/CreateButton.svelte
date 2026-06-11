<script lang="ts">
	import Plus from 'lucide-svelte/icons/plus';
	import type { ComponentType, Snippet } from 'svelte';

	interface Props {
		label: string;
		/** Renders an <a> instead of a <button> when set. */
		href?: string;
		onclick?: (e: MouseEvent) => void;
		/** Override the leading icon (defaults to a Plus). */
		icon?: ComponentType;
		disabled?: boolean;
		class?: string;
		children?: Snippet;
	}

	let {
		label,
		href,
		onclick,
		icon: Icon = Plus,
		disabled = false,
		class: className = '',
		children
	}: Props = $props();
</script>

{#if href}
	<a class="ds-btn ds-btn-primary whitespace-nowrap {className}" {href}>
		<Icon size={16} />
		{label}
		{@render children?.()}
	</a>
{:else}
	<button class="ds-btn ds-btn-primary whitespace-nowrap {className}" {onclick} {disabled}>
		<Icon size={16} />
		{label}
		{@render children?.()}
	</button>
{/if}
