<script lang="ts">
	export let message: string;
	export let href: string;
	export let linkText: string;
</script>

<span>
	{message}
	<a {href} class="font-medium underline" style="color: inherit;">{linkText}</a>
</span>
