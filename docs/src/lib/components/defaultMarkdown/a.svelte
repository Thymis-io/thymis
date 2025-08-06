<script lang="ts">
    import { getContext } from 'svelte';

    // get prefix from context
    const prefix = getContext<string>('prefix') || '';

    let { href, children } = $props();

    let shouldGetPrefixed = $derived(href.startsWith('/') || href.startsWith('./'));

    let finalHref = $derived(
        shouldGetPrefixed ? `${prefix}${href}` : href
    );

</script>
<a
    href={finalHref}
>
    {@render children()}
</a>
