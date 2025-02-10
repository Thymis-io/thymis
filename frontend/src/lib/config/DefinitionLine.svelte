<script lang="ts">
	import { P } from 'flowbite-svelte';
	import TagIcon from 'lucide-svelte/icons/tag';
	import FileCode from 'lucide-svelte/icons/file-code-2';
	import type { Origin } from '$lib/state';

	export let origin: Origin;
	export let value: unknown;
</script>

<div class="flex flex gap-2">
	{#if origin.originContext === 'tag'}
		<TagIcon class="w-5 h-5" />
	{:else if origin.originContext === 'config'}
		<FileCode class="w-5 h-5" />
	{/if}
	<P size="sm">{origin.originName}:</P>
</div>
<P size="sm">{value}</P>
