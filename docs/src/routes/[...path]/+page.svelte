<script lang="ts">
	import { page } from '$app/stores';
	import DocumentationLayout from '../../lib/components/DocumentationLayout.svelte';

	let { data } = $props();
</script>

<DocumentationLayout path={data.path} currentPath={$page.url.pathname} />
