<script lang="ts">
	import { HighlightAuto, LineNumbers } from 'svelte-highlight';
	import ashes from 'svelte-highlight/styles/ashes';

	export let code;
</script>

<svelte:head>
	{@html ashes}
</svelte:head>

<HighlightAuto {code} let:highlighted>
	<LineNumbers {highlighted} />
</HighlightAuto>
