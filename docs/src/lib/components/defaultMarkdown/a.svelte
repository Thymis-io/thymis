<script lang="ts">
	import { getContext } from 'svelte';
	import type { ClassValue } from 'svelte/elements';

	// get prefix from context
	const prefix = getContext<string>('prefix') || '';

	// let { href, children,  } = $props();
	let props = $props();

	let shouldGetPrefixed = $derived(props.href.startsWith('/') || props.href.startsWith('./'));

	let processedHref = $derived(
		props.href.endsWith('.md')
			? props.href.slice(0, -3) // Remove '.md' (3 characters)
			: props.href
	);

	let relativeHref = $derived(
		processedHref.startsWith('./')
			? processedHref.slice(2) // Remove './' (2 characters) to make it relative
			: processedHref
	);

	let finalHref = $derived(shouldGetPrefixed ? `${prefix}${relativeHref}` : relativeHref);
</script>

<a href={finalHref} class={props.class}>
	{@render props.children()}
</a>
