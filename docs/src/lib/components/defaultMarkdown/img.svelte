<script lang="ts">
	import { getContext } from 'svelte';
	import type { ClassValue } from 'svelte/elements';

	let props = $props();
</script>

<img src={props.src} alt={props.alt} class={`shadow-xl ${props.class}`}/>
