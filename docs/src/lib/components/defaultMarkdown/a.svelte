<script lang="ts">
    import { getContext } from 'svelte';
    import type { ClassValue } from 'svelte/elements';


    // get prefix from context
    const prefix = getContext<string>('prefix') || '';

    // let { href, children,  } = $props();
    let props =  $props();

    let shouldGetPrefixed = $derived(props.href.startsWith('/') || props.href.startsWith('./'));

    let finalHref = $derived(
        shouldGetPrefixed ? `${prefix}${props.href}` : props.href
    );

</script>
<a
    href={finalHref}
    class={props.class}
>
    {@render props.children()}
</a>
