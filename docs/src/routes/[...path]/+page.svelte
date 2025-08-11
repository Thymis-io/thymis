<script lang="ts">
	import { page } from '$app/stores';
	import DocumentationLayout from '../../lib/components/DocumentationLayout.svelte';

	let { data } = $props();
</script>

<DocumentationLayout shortPath={data.path} prefixedPath={$page.url.pathname} />
