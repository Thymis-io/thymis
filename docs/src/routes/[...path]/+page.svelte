<script lang="ts">
	import DocumentationLayout from '$lib/components/DocumentationLayout.svelte';

	let { data } = $props();
</script>

<DocumentationLayout path={data.path} />
