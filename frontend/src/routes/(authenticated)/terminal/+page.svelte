<script lang="ts">
	import Terminal from '$lib/terminal/Terminal.svelte';
	import { globalNavSelectedDevice } from '$lib/state';
</script>

<Terminal device={$globalNavSelectedDevice} />
