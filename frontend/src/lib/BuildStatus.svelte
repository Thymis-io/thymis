<script lang="ts">
	import { Button, Modal } from 'flowbite-svelte';
	import { CircleExclamationSolid, TriangleExclamationSolid } from 'svelte-awesome-icons';
	import { buildStatus } from './buildstatus';

	let stdoutModalOpen = false;
	let stderrModalOpen = false;
</script>

<div class="flex justify-between items-center gap-1">
	<span class="dark:text-white">
		Build Status: {$buildStatus?.status}
	</span>
	{#if $buildStatus?.stdout}
		<Button
			outline
			color={'alternative'}
			class="p-2"
			id="stderr"
			on:click={() => (stdoutModalOpen = true)}
		>
			<CircleExclamationSolid color="#0080c0" id="stdout" />
		</Button>
	{/if}
	{#if $buildStatus?.stderr}
		<Button
			outline
			color={'alternative'}
			class="p-2"
			id="stderr"
			on:click={() => (stderrModalOpen = true)}
		>
			<TriangleExclamationSolid color="#c4c400" />
		</Button>
	{/if}
</div>
<Modal title="Standard Out" bind:open={stdoutModalOpen} autoclose outsideclose size="xl">
	<pre class="w-full text-sm font-light z-50 hover:z-50">{$buildStatus?.stdout}</pre>
</Modal>
<Modal title="Standard Error" bind:open={stderrModalOpen} autoclose outsideclose size="xl">
	<pre class="w-full text-sm font-light z-50 hover:z-50">{$buildStatus?.stderr}</pre>
</Modal>
