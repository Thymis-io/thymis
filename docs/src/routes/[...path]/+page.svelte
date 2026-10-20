<script lang="ts">
	import { page } from '$app/state';
	import DocumentationLayout from '../../lib/components/DocumentationLayout.svelte';

	let { data } = $props();
</script>

<DocumentationLayout shortPath={data.path} prefixedPath={page.url.pathname} />
