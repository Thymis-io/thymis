<script lang="ts">
	import { getContext } from 'svelte';
	import type { ClassValue } from 'svelte/elements';

	let props = $props();
    console.log('code', props.code);
</script>
<pre class="{props.class} not-prose">{@render props.children()}</pre>
