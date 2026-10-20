<script lang="ts">
	let { children } = $props();
</script>

<ul class="list-none space-y-1 pl-0 [&_ul]:mt-2 [&_ul]:ml-4">
	{@render children()}
</ul>
