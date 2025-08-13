<script lang="ts">
	import { getContext } from 'svelte';
	import type { ClassValue } from 'svelte/elements';
	import type { writable } from 'svelte/store';

	// get prefix from context
	const prefix = getContext<string>('prefix') || '';
		// get current path
		const prefixedPath = getContext<writable<string>>('prefixedPath') || '';
	const thymisSite = "https://thymis.io";
    // get localized href function from context, can be undefined but then just prepend thymisSite
	const localizeHref = getContext<(href: string) => string>('localizeHref') || ((href: string) => `${thymisSite}${href}`);

	// let { href, children,  } = $props();
	let props = $props();

	// if prefix is prefixedPath <=> we are in index
	let shouldGetPrefixed = $derived(
		props.href.startsWith('/') ||
			props.href.startsWith('./') ||
			props.href.starts ||
			(prefix &&
				$prefixedPath === prefix &&
				// and should start with alphanum
				/^[a-zA-Z0-9]/.test(props.href) &&
				// and should not start with http(s)://
				!/^https?:\/\//.test(props.href))
	);

	// let processedHref = $derived(
	// 	props.href.endsWith('.md')
	// 		? props.href.slice(0, -3) // Remove '.md' (3 characters)
	// 		: props.href
	// );
	// URL can contain a hash, remove .md before the hash
	let processedHref = $derived.by(() => {
		// remove and re-add hash
		const hashIndex = props.href.indexOf('#');
		const hrefWithoutHash = hashIndex !== -1 ? props.href.slice(0, hashIndex) : props.href;
		const hash = hashIndex !== -1 ? props.href.slice(hashIndex) : '';
		return hrefWithoutHash.endsWith('.md') ? hrefWithoutHash.slice(0, -3) + hash : hrefWithoutHash + hash;
	});

	let relativeHref = $derived(
		processedHref.startsWith('./')
			? processedHref.slice(2) // Remove './' (2 characters) to make it relative
			: processedHref
	);

	// if should get prefixed and also begins with alphanum, add a slash
	let addSlash = $derived(
		shouldGetPrefixed && /^[a-zA-Z0-9]/.test(relativeHref) && !relativeHref.startsWith('/')
	);

	let isInternalNonDocsLink = $derived(props.href.startsWith(thymisSite));
	let isExternalLink = $derived(
		(props.href.startsWith('http://') || props.href.startsWith('https://')) && !isInternalNonDocsLink
	);

	// let finalHref = $derived(shouldGetPrefixed ? `${prefix}${relativeHref}` : relativeHref);
	let finalHref = $derived(
		isExternalLink ? props.href : isInternalNonDocsLink ? (
			// remove thymisSite and localize href using localizeHref function
			localizeHref(props.href.slice(thymisSite.length))
		) : shouldGetPrefixed ? `${prefix}${addSlash ? '/' : ''}${relativeHref}` : relativeHref
	);
</script>

<a href={finalHref} class={props.class} target={isExternalLink ? '_blank' : '_self'}>
	{@render props.children()}{#if isExternalLink}
		<i class="fas fa-external-link-alt ml-1 text-gray-400 text-sm"></i>
	{/if}
</a>
