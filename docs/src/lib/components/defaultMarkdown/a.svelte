<script lang="ts">
	import { getContext } from 'svelte';
	import type { ClassValue } from 'svelte/elements';
	import type { writable } from 'svelte/store';

	// get prefix from context
	const prefix = getContext<string>('prefix') || '';
	// get current path
	const prefixedPath = getContext<writable<string>>('prefixedPath') || '';

	// let { href, children,  } = $props();
	let props = $props();

	// if prefix is prefixedPath <=> we are in index
	let shouldGetPrefixed = $derived(
		props.href.startsWith('/') ||
			props.href.startsWith('./') ||
			props.href.starts ||
			(prefix && $prefixedPath === prefix)
	);

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

	// if should get prefixed and also begins with alphanum, add a slash
	let addSlash = $derived(
		shouldGetPrefixed && /^[a-zA-Z0-9]/.test(relativeHref) && !relativeHref.startsWith('/')
	);

	// let finalHref = $derived(shouldGetPrefixed ? `${prefix}${relativeHref}` : relativeHref);
	let finalHref = $derived(
		shouldGetPrefixed
			? `${prefix}${addSlash ? '/' : ''}${relativeHref}`
			: relativeHref
	);
</script>

<a href={finalHref} class={props.class}>
	{@render props.children()}
</a>
