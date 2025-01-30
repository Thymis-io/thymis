<script lang="ts">
	export let columns: number;
	let className = '';
	export { className as class };
</script>

<div class="grid {className}" style="grid-template-columns: repeat({columns}, minmax(0, 1fr));">
	<slot />
</div>
